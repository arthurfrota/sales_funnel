from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..advisor import Advisor
from ..calculators.base import CalculationContext
from ..calculators.digital import DigitalLeadCalculator, DigitalDirectCalculator
from ..calculators.hybrid import HybridCalculator
from ..calculators.offline import (
    OfflineFieldCalculator,
    OfflineInsideCalculator,
    OfflineStoreCalculator,
)
from ..dependencies import get_current_user, get_db
from ..models import Benchmark, Capacity, Channel, Funnel, FunnelMetric, Result, Scenario
from ..schemas import ScenarioCreate, ScenarioRead, ScenarioResult

router = APIRouter(tags=["scenarios"], dependencies=[Depends(get_current_user)])


@router.post("/funnels/{funnel_id}/scenarios", response_model=ScenarioRead)
def create_scenario(funnel_id: int, payload: ScenarioCreate, db: Session = Depends(get_db)) -> ScenarioRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    scenario = Scenario(funnel_id=funnel_id, name=payload.name, overrides_json=payload.overrides)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/scenarios/{scenario_id}", response_model=ScenarioRead)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)) -> ScenarioRead:
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/scenarios/{scenario_id}/calculate", response_model=ScenarioResult)
def calculate_scenario(scenario_id: int, db: Session = Depends(get_db)) -> ScenarioResult:
    scenario = db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    funnel = scenario.funnel
    metrics = {metric.name: metric.value for metric in funnel.metrics}
    capacity = scenario.funnel.capacity
    channels = [channel_to_dict(channel) for channel in funnel.channels]

    overrides = scenario.overrides_json or {}
    metrics.update(overrides.get("metrics", {}))
    capacity_data = capacity_to_dict(capacity)
    capacity_data.update(overrides.get("capacity", {}))
    channels = apply_channel_overrides(channels, overrides.get("channels", []))

    context = CalculationContext(
        mode=funnel.mode,
        submode=funnel.submode,
        meta=overrides.get("meta", funnel.meta),
        ticket=overrides.get("ticket", funnel.ticket),
        dias_uteis=overrides.get("dias_uteis", funnel.dias_uteis),
        ciclo_vendas=overrides.get("ciclo_vendas", funnel.ciclo_vendas),
        metrics=metrics,
        capacity=capacity_data,
        channels=channels,
        overrides=overrides,
    )

    if funnel.mode == "digital":
        if funnel.submode == "direct_purchase":
            receita_estimada, kpis, breakdown = DigitalDirectCalculator(context).run()
        else:
            receita_estimada, kpis, breakdown = DigitalLeadCalculator(context).run()
    elif funnel.mode == "offline":
        if funnel.submode == "loja_b2c":
            receita_estimada, kpis, breakdown = OfflineStoreCalculator(context).run()
        elif funnel.submode == "inside_phone":
            receita_estimada, kpis, breakdown = OfflineInsideCalculator(context).run()
        else:
            receita_estimada, kpis, breakdown = OfflineFieldCalculator(context).run()
    else:
        receita_estimada, kpis, breakdown = HybridCalculator(context).run()

    meta = context.meta
    gap = meta - receita_estimada
    bateu_meta = receita_estimada >= meta

    benchmarks = {
        benchmark.key: benchmark.value
        for benchmark in db.query(Benchmark).filter(Benchmark.sector == funnel.workspace.company.sector)
    }
    advisor = Advisor(benchmarks)
    gargalo, recomendacoes = advisor.evaluate(
        {
            "dias_uteis": context.dias_uteis,
            "leads_atual": sum(channel.get("leads", 0) for channel in channels),
            "trafego_atual": sum(channel.get("visits", 0) for channel in channels),
            "ticket": context.ticket,
            "taxa_global": kpis.get("taxa_global", 0),
            "cpa_medio": sum(channel.get("budget", 0) for channel in channels)
            / max(sum(channel.get("leads", 0) for channel in channels), 1),
            "wip_atual": overrides.get("wip_atual", 0),
            "no_show": capacity_data.get("no_show", 0),
            "vendedores": capacity_data.get("vendedores"),
            "taxa_prop_fech": metrics.get("taxa_prop_fech", 0),
        },
        receita_estimada,
        meta,
        kpis,
        breakdown,
    )

    result = Result(
        scenario_id=scenario.id,
        receita_estimada=receita_estimada,
        gap=gap,
        bateu_meta=bateu_meta,
        gargalo=gargalo,
        recomendacao_json=recomendacoes,
        breakdown_json=breakdown,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return ScenarioResult(
        scenario_id=scenario.id,
        bateu_meta=bateu_meta,
        receita_estimada=receita_estimada,
        gap=gap,
        gargalo=gargalo,
        kpis=kpis,
        recomendacoes=recomendacoes,
        breakdown=breakdown,
    )


def channel_to_dict(channel: Channel) -> dict:
    data = {k: getattr(channel, k) for k in channel.__dict__ if not k.startswith("_") and k not in {"funnel_id", "id", "created_at", "updated_at"}}
    data["name"] = channel.name
    return data


def capacity_to_dict(capacity: Capacity | None) -> dict:
    if not capacity:
        return {}
    return {k: getattr(capacity, k) for k in capacity.__dict__ if not k.startswith("_") and k not in {"funnel_id", "id"}}


def apply_channel_overrides(channels: list[dict], overrides: list[dict]) -> list[dict]:
    channel_map = {channel.get("name"): channel for channel in channels}
    for override in overrides:
        name = override.get("name")
        if name and name in channel_map:
            channel_map[name].update(override)
        elif name:
            channel_map[name] = override
    return list(channel_map.values())
