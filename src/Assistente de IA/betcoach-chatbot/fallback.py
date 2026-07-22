"""Modo básico determinístico, independente do Ollama."""

from __future__ import annotations

import re
from typing import Any

from calculations import implied_probability, potential_return
from risk_detection import normalize

PREFIX = ""


def fallback_response(
    user_message: str,
    knowledge_results: list[dict[str, Any]],
    risk_signals: list[dict[str, str]],
    model_available: bool = False,
) -> str:
    text = normalize(user_message)
    risks = {item["type"] for item in risk_signals}
    if "minor" in risks:
        body = "Para menores de 18 anos, ofereço apenas explicações gerais de matemática e probabilidade, sem orientar ou analisar apostas."
    elif risks & {"essential_money", "borrowing", "limit_evasion", "desperation"}:
        body = "Não é seguro apostar com dinheiro essencial, empréstimos ou tentando burlar limites. O passo mais seguro é pausar e buscar apoio de alguém de confiança."
    elif risks & {"chasing_losses", "stake_increase_after_losses"}:
        body = "Dobrar o valor após uma perda aumenta a exposição e não garante recuperação. Isso pode indicar perseguição de prejuízo; pause e revise seus limites."
    elif any(phrase in text for phrase in ("aposta certa", "aposta garantida", "sem risco")):
        body = "Não existe aposta garantida e eu não posso prometer resultado. Posso explicar odds, probabilidades, riscos e dados históricos."
    elif "roi" in text:
        body = "ROI mede o lucro líquido em relação ao valor apostado nas apostas encerradas: lucro líquido ÷ total apostado × 100. ROI passado não garante resultado futuro."
    elif "banca" in text:
        body = "Banca é o valor separado exclusivamente para apostas, sem incluir dinheiro de despesas essenciais. Limites reduzem a exposição, mas não eliminam o risco."
    elif "probabilidade implicita" in text:
        body = "A probabilidade implícita de uma odd decimal é calculada por 1 ÷ odd. Por exemplo, odd 2,00 corresponde a 50%."
    else:
        odd_match = re.search(r"\bodd(?:s)?\s*(?:de|=)?\s*(\d+(?:[.,]\d+)?)", text)
        if odd_match:
            odd = float(odd_match.group(1).replace(",", "."))
            if odd <= 1:
                body = "A odd informada é inválida; use um valor decimal maior que 1."
            else:
                body = (
                    f"Uma odd decimal de {odd:.2f} daria retorno total potencial de R$ {potential_return(odd, 10):.2f} "
                    f"para R$ 10,00. A probabilidade implícita é {implied_probability(odd) * 100:.2f}%. "
                    "Isso não garante o resultado."
                )
        elif "o que e odd" in text or text.strip() == "odd":
            body = "Odd decimal é o multiplicador do retorno total potencial. Ela também permite calcular uma probabilidade implícita, mas não prova a chance real."
        elif knowledge_results:
            body = "\n\n".join(
                f"Fonte local: {item['source']}\n{item['content']}" for item in knowledge_results[:2]
            )
        else:
            body = "Não encontrei dados locais suficientes para responder com segurança. Tente reformular ou consulte a base de conhecimento."
    return body
