from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class Token(BaseModel):
    token: str
    token_type: str = "bearer"
    user: "UserRead"


class TokenRequest(BaseModel):
    email: str
    password: str


class UserBase(BaseModel):
    name: str
    email: str
    role: str = "viewer"


class UserCreate(UserBase):
    workspace_id: int
    password: str


class UserRead(UserBase):
    id: int
    workspace_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    name: str
    sector: Optional[str] = None
    country: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    company_id: int
    name: str


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceRead(WorkspaceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FunnelBase(BaseModel):
    workspace_id: int
    mode: str
    submode: Optional[str] = None
    ticket: float
    meta: float
    dias_uteis: int
    ciclo_vendas: int

    @validator("ticket", "meta", "dias_uteis", "ciclo_vendas")
    def positive_numbers(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Value must be non-negative")
        return value


class FunnelCreate(FunnelBase):
    metrics: dict[str, float] = Field(default_factory=dict)
    capacity: Optional[dict[str, Any]] = None
    channels: list[dict[str, Any]] = Field(default_factory=list)


class FunnelUpdate(BaseModel):
    mode: Optional[str]
    submode: Optional[str]
    ticket: Optional[float]
    meta: Optional[float]
    dias_uteis: Optional[int]
    ciclo_vendas: Optional[int]


class FunnelMetricUpdate(BaseModel):
    metrics: dict[str, float]


class CapacityUpdate(BaseModel):
    capacity: dict[str, Any]


class ChannelBase(BaseModel):
    type: str
    name: str
    mix: Optional[float] = None
    budget: Optional[float] = None
    cpc: Optional[float] = None
    cpm: Optional[float] = None
    ctr: Optional[float] = None
    cr_visit_lead: Optional[float] = None
    cr_visit_add: Optional[float] = None
    cr_cart_checkout: Optional[float] = None
    cr_checkout_compra: Optional[float] = None
    cpa_lead: Optional[float] = None
    roas_target: Optional[float] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(ChannelBase):
    type: Optional[str] = None
    name: Optional[str] = None


class ChannelRead(ChannelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FunnelRead(FunnelBase):
    id: int
    created_at: datetime
    metrics: dict[str, float]
    capacity: Optional[dict[str, Any]]
    channels: list[ChannelRead]

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    funnel_id: int
    name: str
    overrides: Optional[dict[str, Any]] = Field(default_factory=dict)


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioRead(ScenarioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScenarioResult(BaseModel):
    scenario_id: int
    bateu_meta: bool
    receita_estimada: float
    gap: float
    gargalo: Optional[str]
    kpis: dict[str, Any]
    recomendacoes: list[dict[str, Any]]
    breakdown: dict[str, Any]


class BenchmarkRead(BaseModel):
    id: int
    sector: str
    key: str
    value: float

    class Config:
        from_attributes = True


class BenchmarkUpdate(BaseModel):
    sector: str
    key: str
    value: float
