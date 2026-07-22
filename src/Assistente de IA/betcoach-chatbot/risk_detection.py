"""Regras simples e explicáveis de proteção ao usuário."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in value if not unicodedata.combining(char))


def detect_risk_signals(
    user_message: str,
    bets: list[dict[str, Any]],
    bankroll: float,
    proposed_stake: float | None = None,
) -> list[dict[str, str]]:
    text = normalize(user_message)
    signals: list[dict[str, str]] = []

    def add(kind: str, description: str, severity: str = "high") -> None:
        if not any(item["type"] == kind for item in signals):
            signals.append({"type": kind, "severity": severity, "description": description})

    if any(phrase in text for phrase in ("dobrar para recuperar", "dobrar agora", "recuperar o prejuizo", "recuperar hoje")):
        add("chasing_losses", "Possível tentativa de perseguir perdas.")
    if any(phrase in text for phrase in ("dinheiro do aluguel", "dinheiro da comida", "salario inteiro")):
        add("essential_money", "Possível uso de dinheiro essencial.")
    if "emprestimo" in text or "cartao emprestado" in text:
        add("borrowing", "Menção a empréstimo ou crédito de terceiros para apostar.")
    if any(phrase in text for phrase in ("burlar meu limite", "burlar o limite", "contornar autoexclusao")):
        add("limit_evasion", "Tentativa de burlar limite ou autoexclusão.")
    if any(phrase in text for phrase in ("estou desesperado", "minha ultima chance", "nao posso perder")):
        add("desperation", "Linguagem de desespero relacionada à aposta.")

    ages = [
        int(match.group(1))
        for pattern in (r"\btenho\s+(\d{1,2})\s+anos", r"\bidade\s*[:=]?\s*(\d{1,2})")
        for match in re.finditer(pattern, text)
    ]
    if any(age < 18 for age in ages):
        add("minor", "Declaração explícita de menoridade.")

    if proposed_stake is not None and bankroll > 0 and proposed_stake / bankroll > 0.10:
        add("high_exposure", "A stake proposta supera 10% da banca.")

    recent = sorted(bets, key=lambda item: str(item.get("bet_date", "")), reverse=True)[:5]
    prior_stakes = [float(item.get("stake", 0)) for item in recent if float(item.get("stake", 0)) > 0]
    two_losses = len(recent) >= 2 and all(item.get("status") == "perdida" for item in recent[:2])
    if proposed_stake and prior_stakes and two_losses:
        average = sum(prior_stakes) / len(prior_stakes)
        if proposed_stake > average * 1.5:
            add("stake_increase_after_losses", "Aumento significativo de stake após perdas.")
    return signals

