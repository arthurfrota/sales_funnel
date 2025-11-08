from __future__ import annotations

from typing import Any, Dict, List, Tuple


class Advisor:
    def __init__(self, benchmarks: Dict[str, float] | None = None):
        self.benchmarks = benchmarks or {}

    def evaluate(
        self,
        context: Dict[str, Any],
        receita_estimada: float,
        meta: float,
        kpis: Dict[str, Any],
        breakdown: Dict[str, Any],
    ) -> Tuple[str | None, List[Dict[str, Any]]]:
        gargalo = None
        recomendacoes: List[Dict[str, Any]] = []

        if self._is_capacidade_gargalo(context, kpis):
            gargalo = "Capacidade"
            recomendacoes.append(self._recomendacao_capacidade(context, kpis))
        elif self._is_demanda_gargalo(context, kpis):
            gargalo = "Demanda"
            recomendacoes.extend(self._recomendacao_demanda(context, kpis))
        elif self._is_conversao_gargalo(kpis):
            gargalo = "Conversao"
            recomendacoes.extend(self._recomendacao_conversao(context, kpis))
        elif self._is_velocidade_gargalo(context, kpis):
            gargalo = "Velocidade"
            recomendacoes.append(self._recomendacao_velocidade(context, kpis))
        elif self._is_noshow_gargalo(context):
            gargalo = "No-show"
            recomendacoes.append(self._recomendacao_noshow(context))

        if gargalo is None and receita_estimada < meta:
            gargalo = "Conversao"

        return gargalo, [r for r in recomendacoes if r]

    def _is_capacidade_gargalo(self, context: Dict[str, Any], kpis: Dict[str, Any]) -> bool:
        capacidade = kpis.get("capacidade_reunioes_mes")
        reunioes_nec = kpis.get("reunioes_necessarias")
        if capacidade is not None and reunioes_nec is not None:
            return reunioes_nec > capacidade
        vendas_max = kpis.get("vendas_maximas_dia")
        vendas_nec = kpis.get("vendas_necessarias")
        dias_uteis = context.get("dias_uteis", 0)
        if vendas_max and vendas_nec:
            return vendas_max * dias_uteis < vendas_nec
        return False

    def _is_demanda_gargalo(self, context: Dict[str, Any], kpis: Dict[str, Any]) -> bool:
        leads_nec = kpis.get("leads_necessarios")
        leads_atual = context.get("leads_atual")
        if leads_nec and leads_atual is not None:
            return leads_nec > leads_atual
        trafego_nec = kpis.get("trafego_necessario")
        trafego_atual = context.get("trafego_atual")
        if trafego_nec and trafego_atual is not None:
            return trafego_nec > trafego_atual
        return False

    def _is_conversao_gargalo(self, kpis: Dict[str, Any]) -> bool:
        for key, value in kpis.items():
            if key.startswith("taxa") or key.startswith("cr_"):
                benchmark = self.benchmarks.get(key)
                if benchmark is not None and value < benchmark:
                    return True
        return False

    def _is_velocidade_gargalo(self, context: Dict[str, Any], kpis: Dict[str, Any]) -> bool:
        wip_min = kpis.get("wip_minimo")
        wip_atual = context.get("wip_atual")
        if wip_min and wip_atual is not None:
            return wip_atual < wip_min
        return False

    def _is_noshow_gargalo(self, context: Dict[str, Any]) -> bool:
        no_show = context.get("no_show")
        benchmark = self.benchmarks.get("no_show")
        if benchmark is not None and no_show is not None:
            return no_show > benchmark
        return False

    def _recomendacao_capacidade(self, context: Dict[str, Any], kpis: Dict[str, Any]):
        vendedores = context.get("vendedores", 0)
        impacto = kpis.get("ticket", 0) * context.get("taxa_prop_fech", 0)
        return {
            "tipo": "capacidade",
            "acao": "+1 vendedor",
            "impacto_receita": max(impacto, 0),
        }

    def _recomendacao_demanda(self, context: Dict[str, Any], kpis: Dict[str, Any]):
        recomendacoes = []
        gap_leads = kpis.get("leads_necessarios", 0) - context.get("leads_atual", 0)
        if gap_leads > 0:
            custo_medio = context.get("cpa_medio", 0)
            recomendacoes.append(
                {
                    "tipo": "demanda",
                    "acao": f"Adicionar budget para {int(gap_leads)} leads",
                    "impacto_receita": gap_leads * context.get("ticket", 0) * context.get(
                        "taxa_global", 0
                    ),
                    "investimento": gap_leads * custo_medio,
                }
            )
        return recomendacoes

    def _recomendacao_conversao(self, context: Dict[str, Any], kpis: Dict[str, Any]):
        recomendacoes = []
        for key, benchmark in self.benchmarks.items():
            valor = kpis.get(key)
            if valor is not None and valor < benchmark:
                recomendacoes.append(
                    {
                        "tipo": "conversao",
                        "acao": f"Otimizar {key}",
                        "impacto_receita": (benchmark - valor)
                        * context.get("leads_atual", 0)
                        * context.get("ticket", 0),
                    }
                )
        return recomendacoes

    def _recomendacao_velocidade(self, context: Dict[str, Any], kpis: Dict[str, Any]):
        wip_min = kpis.get("wip_minimo", 0)
        wip_atual = context.get("wip_atual", 0)
        delta = max(wip_min - wip_atual, 0)
        return {
            "tipo": "velocidade",
            "acao": "Aumentar follow-ups para elevar WIP",
            "impacto_receita": delta * context.get("ticket", 0),
        }

    def _recomendacao_noshow(self, context: Dict[str, Any]):
        no_show = context.get("no_show", 0)
        target = self.benchmarks.get("no_show", 0.1)
        delta = max(no_show - target, 0)
        return {
            "tipo": "no_show",
            "acao": "Implementar confirmações 24h/1h",
            "impacto_receita": delta * context.get("ticket", 0) * context.get("leads_atual", 0),
        }
