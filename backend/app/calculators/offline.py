from __future__ import annotations

from typing import Any, Dict, Tuple

from .base import BaseCalculator, safe_get


class OfflineFieldCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        m = self.context.metrics
        cap = self.context.capacity

        taxa_prop_fech = safe_get(m, "taxa_prop_fech")
        taxa_reuniao_prop = safe_get(m, "taxa_reuniao_prop")
        taxa_contato_reuniao = safe_get(m, "taxa_contato_reuniao")
        no_show = safe_get(cap, "no_show", 0.0)

        vendas_nec = self.context.meta / self.context.ticket if self.context.ticket else 0
        propostas_nec = vendas_nec / taxa_prop_fech if taxa_prop_fech else 0
        reunioes_nec = propostas_nec / taxa_reuniao_prop if taxa_reuniao_prop else 0
        contatos_nec = reunioes_nec / taxa_contato_reuniao if taxa_contato_reuniao else 0

        ligacoes_dia = safe_get(cap, "ligacoes_dia")
        sdrs = safe_get(cap, "sdrs")
        reunioes_geradas = ligacoes_dia * self.context.dias_uteis * sdrs * safe_get(
            m, "cr_ligacao_reuniao", taxa_contato_reuniao
        )
        reunioes_validas = reunioes_geradas * (1 - no_show)

        vendedores = safe_get(cap, "vendedores")
        visitas_dia = safe_get(cap, "visitas_dia")
        capacidade_visitas_dia = vendedores * visitas_dia
        capacidade_reunioes_mes = capacidade_visitas_dia * self.context.dias_uteis * (1 - no_show)

        contatos_atuais = safe_get(cap, "contatos_atuais", reunioes_validas / taxa_contato_reuniao if taxa_contato_reuniao else 0)
        receita_estimada = (
            contatos_atuais * taxa_contato_reuniao * taxa_reuniao_prop * taxa_prop_fech
        ) * self.context.ticket

        vendas_dia = vendas_nec / self.context.dias_uteis if self.context.dias_uteis else 0
        wip_min = vendas_dia * self.context.ciclo_vendas

        breakdown = {
            "offline_field_b2b": {
                "propostas_necessarias": propostas_nec,
                "reunioes_necessarias": reunioes_nec,
                "contatos_necessarios": contatos_nec,
                "reunioes_validas": reunioes_validas,
                "capacidade_reunioes_mes": capacidade_reunioes_mes,
            }
        }
        kpis = {
            "vendas_necessarias": vendas_nec,
            "propostas_necessarias": propostas_nec,
            "reunioes_necessarias": reunioes_nec,
            "contatos_necessarios": contatos_nec,
            "capacidade_reunioes_mes": capacidade_reunioes_mes,
            "wip_minimo": wip_min,
        }
        return receita_estimada, kpis, breakdown


class OfflineStoreCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        m = self.context.metrics
        cap = self.context.capacity

        taxa_abordagem = safe_get(m, "taxa_abordagem")
        taxa_demo = safe_get(m, "taxa_demo")
        taxa_fechamento = safe_get(m, "taxa_fechamento")
        cr_global = taxa_abordagem * taxa_demo * taxa_fechamento

        vendas_nec = self.context.meta / self.context.ticket if self.context.ticket else 0
        trafego_nec = vendas_nec / cr_global if cr_global else 0

        vendedores = safe_get(cap, "vendedores")
        atendimentos_simultaneos = safe_get(cap, "atendimentos_simultaneos")
        horas_loja = safe_get(cap, "horas_loja")
        tempo_medio = safe_get(cap, "tempo_medio_atendimento", 1)
        capacidade_atendimento_dia = (
            vendedores * atendimentos_simultaneos * (horas_loja / tempo_medio if tempo_medio else 0)
        )
        vendas_max_dia = capacidade_atendimento_dia * taxa_fechamento
        receita_estimada = vendas_max_dia * self.context.dias_uteis * self.context.ticket

        breakdown = {
            "offline_loja_b2c": {
                "cr_global": cr_global,
                "trafego_necessario": trafego_nec,
                "capacidade_atendimento_dia": capacidade_atendimento_dia,
                "vendas_max_dia": vendas_max_dia,
            }
        }
        kpis = {
            "vendas_necessarias": vendas_nec,
            "trafego_necessario": trafego_nec,
            "capacidade_atendimento_dia": capacidade_atendimento_dia,
            "vendas_maximas_dia": vendas_max_dia,
        }
        return receita_estimada, kpis, breakdown


class OfflineInsideCalculator(BaseCalculator):
    def run(self) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
        m = self.context.metrics
        cap = self.context.capacity

        taxa_prop_fech = safe_get(m, "taxa_prop_fech")
        taxa_contato_reuniao = safe_get(m, "taxa_contato_reuniao")
        taxa_discagem_contato = safe_get(m, "taxa_discagem_contato")

        vendas_nec = self.context.meta / self.context.ticket if self.context.ticket else 0
        propostas_nec = vendas_nec / taxa_prop_fech if taxa_prop_fech else 0
        reunioes_nec = propostas_nec / taxa_contato_reuniao if taxa_contato_reuniao else 0
        contatos_nec = reunioes_nec / taxa_discagem_contato if taxa_discagem_contato else 0

        agentes = safe_get(cap, "agentes")
        discagens_hora = safe_get(cap, "discagens_hora", 0)
        horas_dia = safe_get(cap, "horas_dia", 0)
        discagens_possiveis = agentes * discagens_hora * horas_dia * self.context.dias_uteis
        contatos_gerados = discagens_possiveis * taxa_discagem_contato
        no_show = safe_get(cap, "no_show", 0.0)
        reunioes_validas = contatos_gerados * taxa_contato_reuniao * (1 - no_show)

        receita_estimada = (
            contatos_gerados
            * taxa_contato_reuniao
            * (1 - no_show)
            * taxa_prop_fech
            * self.context.ticket
        )

        breakdown = {
            "offline_inside_phone": {
                "propostas_necessarias": propostas_nec,
                "reunioes_necessarias": reunioes_nec,
                "contatos_necessarios": contatos_nec,
                "contatos_gerados": contatos_gerados,
                "reunioes_validas": reunioes_validas,
            }
        }
        kpis = {
            "vendas_necessarias": vendas_nec,
            "propostas_necessarias": propostas_nec,
            "contatos_necessarios": contatos_nec,
            "discagens_possiveis": discagens_possiveis,
        }
        return receita_estimada, kpis, breakdown
