from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CalculationContext:
    mode: str
    submode: str | None
    meta: float
    ticket: float
    dias_uteis: int
    ciclo_vendas: int
    metrics: Dict[str, float]
    capacity: Dict[str, Any]
    channels: list[Dict[str, Any]]
    overrides: Dict[str, Any]


class CalculationResult(Dict[str, Any]):
    pass


class BaseCalculator:
    def __init__(self, context: CalculationContext):
        self.context = context

    def run(self) -> tuple[float, dict[str, Any], dict[str, Any]]:
        raise NotImplementedError


def safe_get(mapping: Dict[str, Any], key: str, default: float = 0.0) -> float:
    value = mapping.get(key, default)
    if value is None:
        return default
    return float(value)
