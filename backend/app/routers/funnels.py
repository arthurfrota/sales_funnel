from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy.inspection import inspect

from ..dependencies import get_current_user, get_db
from ..models import Capacity, Channel, Funnel, FunnelMetric
from ..schemas import (
    CapacityUpdate,
    ChannelCreate,
    ChannelRead,
    ChannelUpdate,
    FunnelCreate,
    FunnelMetricUpdate,
    FunnelRead,
    FunnelUpdate,
)

router = APIRouter(tags=["funnels"], dependencies=[Depends(get_current_user)])


@router.post("/funnels", response_model=FunnelRead)
def create_funnel(payload: FunnelCreate, db: Session = Depends(get_db)) -> FunnelRead:
    funnel = Funnel(
        workspace_id=payload.workspace_id,
        mode=payload.mode,
        submode=payload.submode,
        ticket=payload.ticket,
        meta=payload.meta,
        dias_uteis=payload.dias_uteis,
        ciclo_vendas=payload.ciclo_vendas,
    )
    db.add(funnel)
    db.flush()

    for name, value in payload.metrics.items():
        db.add(FunnelMetric(funnel_id=funnel.id, name=name, value=value))

    if payload.capacity:
        db.add(Capacity(funnel_id=funnel.id, **payload.capacity))

    for channel_data in payload.channels:
        db.add(Channel(funnel_id=funnel.id, **channel_data))

    db.commit()
    db.refresh(funnel)
    return serialize_funnel(funnel)


@router.get("/funnels/{funnel_id}", response_model=FunnelRead)
def get_funnel(funnel_id: int, db: Session = Depends(get_db)) -> FunnelRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    return serialize_funnel(funnel)


@router.patch("/funnels/{funnel_id}", response_model=FunnelRead)
def update_funnel(funnel_id: int, payload: FunnelUpdate, db: Session = Depends(get_db)) -> FunnelRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(funnel, field, value)
    db.commit()
    db.refresh(funnel)
    return serialize_funnel(funnel)


@router.put("/funnels/{funnel_id}/metrics", response_model=FunnelRead)
def update_metrics(funnel_id: int, payload: FunnelMetricUpdate, db: Session = Depends(get_db)) -> FunnelRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    db.query(FunnelMetric).filter(FunnelMetric.funnel_id == funnel_id).delete()
    for key, value in payload.metrics.items():
        db.add(FunnelMetric(funnel_id=funnel_id, name=key, value=value))
    db.commit()
    db.refresh(funnel)
    return serialize_funnel(funnel)


@router.put("/funnels/{funnel_id}/capacity", response_model=FunnelRead)
def update_capacity(funnel_id: int, payload: CapacityUpdate, db: Session = Depends(get_db)) -> FunnelRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    if funnel.capacity:
        for field, value in payload.capacity.items():
            setattr(funnel.capacity, field, value)
    else:
        db.add(Capacity(funnel_id=funnel_id, **payload.capacity))
    db.commit()
    db.refresh(funnel)
    return serialize_funnel(funnel)


@router.post("/funnels/{funnel_id}/channels", response_model=ChannelRead)
def create_channel(funnel_id: int, payload: ChannelCreate, db: Session = Depends(get_db)) -> ChannelRead:
    funnel = db.get(Funnel, funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="Funnel not found")
    channel = Channel(funnel_id=funnel_id, **payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.patch("/channels/{channel_id}", response_model=ChannelRead)
def update_channel(channel_id: int, payload: ChannelUpdate, db: Session = Depends(get_db)) -> ChannelRead:
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)) -> dict:
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()
    return {"status": "deleted"}


def serialize_funnel(funnel: Funnel) -> FunnelRead:
    metrics = {metric.name: metric.value for metric in funnel.metrics}
    capacity = serialize_capacity(funnel.capacity)
    channels = list(funnel.channels)
    return FunnelRead(
        id=funnel.id,
        workspace_id=funnel.workspace_id,
        mode=funnel.mode,
        submode=funnel.submode,
        ticket=funnel.ticket,
        meta=funnel.meta,
        dias_uteis=funnel.dias_uteis,
        ciclo_vendas=funnel.ciclo_vendas,
        created_at=funnel.created_at,
        metrics=metrics,
        capacity=capacity,
        channels=channels,
    )


def serialize_capacity(capacity: Capacity | None) -> dict | None:
    if not capacity:
        return None
    mapper = inspect(capacity.__class__)
    excluded = {"id", "funnel_id"}
    return {column.key: getattr(capacity, column.key) for column in mapper.columns if column.key not in excluded}
