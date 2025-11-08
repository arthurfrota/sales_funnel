from __future__ import annotations

from typing import Any, Dict, Tuple

from .base import BaseCalculator, CalculationContext
from .digital import DigitalLeadCalculator, DigitalDirectCalculator
from .offline import OfflineFieldCalculator, OfflineStoreCalculator, OfflineInsideCalculator


class HybridCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        submode = self.context.submode or "lead_driven+field_b2b"
        digital_mode, offline_mode = submode.split("+") if "+" in submode else (
            "lead_driven",
            "field_b2b",
        )

        digital_context = CalculationContext(
            mode="digital",
            submode=digital_mode,
            meta=self.context.meta,
            ticket=self.context.ticket,
            dias_uteis=self.context.dias_uteis,
            ciclo_vendas=self.context.ciclo_vendas,
            metrics=self.context.metrics.get("digital", self.context.metrics),
            capacity=self.context.capacity.get("digital", {}),
            channels=self.context.channels,
            overrides=self.context.overrides.get("digital", {}),
        )
        offline_context = CalculationContext(
            mode="offline",
            submode=offline_mode,
            meta=self.context.meta,
            ticket=self.context.ticket,
            dias_uteis=self.context.dias_uteis,
            ciclo_vendas=self.context.ciclo_vendas,
            metrics=self.context.metrics.get("offline", self.context.metrics),
            capacity=self.context.capacity.get("offline", self.context.capacity),
            channels=self.context.channels,
            overrides=self.context.overrides.get("offline", {}),
        )

        digital_result = self._run_digital(digital_context)
        offline_result = self._run_offline(offline_context)

        receita = digital_result[0] + offline_result[0]
        kpis = {
            "receita_digital": digital_result[0],
            "receita_offline": offline_result[0],
        }
        kpis.update({f"digital_{k}": v for k, v in digital_result[1].items()})
        kpis.update({f"offline_{k}": v for k, v in offline_result[1].items()})

        breakdown = {
            "digital": digital_result[2],
            "offline": offline_result[2],
        }
        return receita, kpis, breakdown

    def _run_digital(self, context: CalculationContext):
        if context.submode == "direct_purchase":
            calc = DigitalDirectCalculator(context)
        else:
            calc = DigitalLeadCalculator(context)
        return calc.run()

    def _run_offline(self, context: CalculationContext):
        submode = context.submode or "field_b2b"
        if submode == "loja_b2c":
            calc = OfflineStoreCalculator(context)
        elif submode == "inside_phone":
            calc = OfflineInsideCalculator(context)
        else:
            calc = OfflineFieldCalculator(context)
        return calc.run()
