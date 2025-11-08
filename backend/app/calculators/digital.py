from __future__ import annotations

from typing import Any, Dict, Tuple

from .base import BaseCalculator, CalculationContext, safe_get


class DigitalLeadCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        metrics = self.context.metrics
        channels = self.context.channels

        taxa_lead_opp = safe_get(metrics, "taxa_lead_opp")
        taxa_opp_prop = safe_get(metrics, "taxa_opp_prop")
        taxa_prop_fech = safe_get(metrics, "taxa_prop_fech")

        taxa_global = taxa_lead_opp * taxa_opp_prop * taxa_prop_fech
        vendas_nec = self.context.meta / self.context.ticket if self.context.ticket else 0
        leads_necessarios = 0.0
        if taxa_global > 0:
            leads_necessarios = vendas_nec / taxa_global

        receita_estimada = 0.0
        budget_cpa = 0.0
        budget_cpc = 0.0
        visits_estimados = 0.0
        for channel in channels:
            leads = float(channel.get("leads", 0) or 0)
            receita_estimada += leads * taxa_global * self.context.ticket
            mix = safe_get(channel, "mix", 0.0)
            cpa_lead = safe_get(channel, "cpa_lead", 0.0)
            budget_cpa += leads_necessarios * mix * cpa_lead
            cr_visit_lead = safe_get(channel, "cr_visit_lead", 0.0)
            cpc = safe_get(channel, "cpc", 0.0)
            if cr_visit_lead > 0:
                budget_cpc += (leads_necessarios * mix / cr_visit_lead) * cpc
            visits_estimados += safe_get(channel, "visits", 0.0)

        breakdown = {
            "digital_lead_driven": {
                "taxa_global": taxa_global,
                "leads_necessarios": leads_necessarios,
                "budget_cpa": budget_cpa,
                "budget_cpc": budget_cpc,
                "visitas_estimadas": visits_estimados,
            }
        }

        kpis = {
            "taxa_global": taxa_global,
            "vendas_necessarias": vendas_nec,
            "leads_necessarios": leads_necessarios,
            "budget_necessario_cpa": budget_cpa,
            "budget_necessario_cpc": budget_cpc,
        }
        return receita_estimada, kpis, breakdown


class DigitalDirectCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        metrics = self.context.metrics
        channels = self.context.channels

        cr_visit_add = safe_get(metrics, "cr_visit_add")
        cr_cart_checkout = safe_get(metrics, "cr_cart_checkout")
        cr_checkout_compra = safe_get(metrics, "cr_checkout_compra")
        cr_visit_compra = safe_get(metrics, "cr_visit_compra")

        cr_compra = cr_visit_compra or (
            cr_visit_add * cr_cart_checkout * cr_checkout_compra
        )

        vendas_nec = self.context.meta / self.context.ticket if self.context.ticket else 0
        visits_nec = vendas_nec / cr_compra if cr_compra else 0

        receita_estimada = 0.0
        breakdown_channels: Dict[str, Any] = {}
        for channel in channels:
            visits = safe_get(channel, "visits", 0.0)
            budget = safe_get(channel, "budget", 0.0)
            cr_channel = safe_get(channel, "cr_compra", cr_compra)
            ticket = self.context.ticket
            vendas_channel = visits * cr_channel
            receita_channel = vendas_channel * ticket
            roas = receita_channel / budget if budget else 0.0
            receita_estimada += receita_channel
            breakdown_channels[channel.get("name", "channel")] = {
                "visitas": visits,
                "conversao": cr_channel,
                "vendas": vendas_channel,
                "receita": receita_channel,
                "roas": roas,
            }

        breakdown = {
            "digital_direct_purchase": {
                "cr_compra": cr_compra,
                "visitas_necessarias": visits_nec,
                "canais": breakdown_channels,
            }
        }
        kpis = {
            "cr_compra": cr_compra,
            "vendas_necessarias": vendas_nec,
            "visitas_necessarias": visits_nec,
        }

        return receita_estimada, kpis, breakdown
