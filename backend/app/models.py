from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(64))

    workspaces: Mapped[list[Workspace]] = relationship("Workspace", back_populates="company")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    company: Mapped[Company] = relationship("Company", back_populates="workspaces")
    users: Mapped[list[User]] = relationship("User", back_populates="workspace")
    funnels: Mapped[list[Funnel]] = relationship("Funnel", back_populates="workspace")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="users")


class Funnel(Base, TimestampMixin):
    __tablename__ = "funnels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    submode: Mapped[Optional[str]] = mapped_column(String(50))
    ticket: Mapped[float] = mapped_column(Float, nullable=False)
    meta: Mapped[float] = mapped_column(Float, nullable=False)
    dias_uteis: Mapped[int] = mapped_column(Integer, nullable=False)
    ciclo_vendas: Mapped[int] = mapped_column(Integer, nullable=False)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="funnels")
    metrics: Mapped[list[FunnelMetric]] = relationship(
        "FunnelMetric", back_populates="funnel", cascade="all, delete-orphan"
    )
    channels: Mapped[list[Channel]] = relationship(
        "Channel", back_populates="funnel", cascade="all, delete-orphan"
    )
    capacity: Mapped[Optional[Capacity]] = relationship(
        "Capacity", back_populates="funnel", cascade="all, delete-orphan", uselist=False
    )
    scenarios: Mapped[list[Scenario]] = relationship(
        "Scenario", back_populates="funnel", cascade="all, delete-orphan"
    )


class FunnelMetric(Base):
    __tablename__ = "funnel_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    funnel_id: Mapped[int] = mapped_column(ForeignKey("funnels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    funnel: Mapped[Funnel] = relationship("Funnel", back_populates="metrics")


class Channel(Base, TimestampMixin):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    funnel_id: Mapped[int] = mapped_column(ForeignKey("funnels.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mix: Mapped[Optional[float]] = mapped_column(Float)
    budget: Mapped[Optional[float]] = mapped_column(Float)
    cpc: Mapped[Optional[float]] = mapped_column(Float)
    cpm: Mapped[Optional[float]] = mapped_column(Float)
    ctr: Mapped[Optional[float]] = mapped_column(Float)
    cr_visit_lead: Mapped[Optional[float]] = mapped_column(Float)
    cr_visit_add: Mapped[Optional[float]] = mapped_column(Float)
    cr_cart_checkout: Mapped[Optional[float]] = mapped_column(Float)
    cr_checkout_compra: Mapped[Optional[float]] = mapped_column(Float)
    cpa_lead: Mapped[Optional[float]] = mapped_column(Float)
    roas_target: Mapped[Optional[float]] = mapped_column(Float)

    funnel: Mapped[Funnel] = relationship("Funnel", back_populates="channels")


class Capacity(Base):
    __tablename__ = "capacity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    funnel_id: Mapped[int] = mapped_column(ForeignKey("funnels.id"), nullable=False)
    vendedores: Mapped[Optional[int]] = mapped_column(Integer)
    visitas_dia: Mapped[Optional[float]] = mapped_column(Float)
    sdrs: Mapped[Optional[int]] = mapped_column(Integer)
    ligacoes_dia: Mapped[Optional[float]] = mapped_column(Float)
    horas_loja: Mapped[Optional[float]] = mapped_column(Float)
    tempo_medio_atendimento: Mapped[Optional[float]] = mapped_column(Float)
    atendimentos_simultaneos: Mapped[Optional[float]] = mapped_column(Float)
    horas_dia: Mapped[Optional[float]] = mapped_column(Float)
    agentes: Mapped[Optional[int]] = mapped_column(Integer)
    no_show: Mapped[Optional[float]] = mapped_column(Float)

    funnel: Mapped[Funnel] = relationship("Funnel", back_populates="capacity")


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    funnel_id: Mapped[int] = mapped_column(ForeignKey("funnels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    overrides_json: Mapped[Optional[dict]] = mapped_column(JSON)

    funnel: Mapped[Funnel] = relationship("Funnel", back_populates="scenarios")
    results: Mapped[list[Result]] = relationship(
        "Result", back_populates="scenario", cascade="all, delete-orphan"
    )


class Result(Base, TimestampMixin):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False)
    receita_estimada: Mapped[float] = mapped_column(Float, nullable=False)
    gap: Mapped[float] = mapped_column(Float, nullable=False)
    bateu_meta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    gargalo: Mapped[Optional[str]] = mapped_column(String(50))
    recomendacao_json: Mapped[Optional[dict]] = mapped_column(JSON)
    breakdown_json: Mapped[Optional[dict]] = mapped_column(JSON)

    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="results")


class Benchmark(Base, TimestampMixin):
    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = ({"sqlite_autoincrement": True},)
