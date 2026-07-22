"""Cálculos educacionais de odds."""

from __future__ import annotations


def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1:
        raise ValueError("A odd deve ser maior que 1.")
    return 1 / decimal_odds


def potential_return(decimal_odds: float, stake: float) -> float:
    if decimal_odds <= 1:
        raise ValueError("A odd deve ser maior que 1.")
    if stake < 0:
        raise ValueError("A stake não pode ser negativa.")
    return decimal_odds * stake

