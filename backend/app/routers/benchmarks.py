from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import Benchmark
from ..schemas import BenchmarkRead, BenchmarkUpdate

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[BenchmarkRead])
def list_benchmarks(sector: str | None = None, db: Session = Depends(get_db)) -> list[BenchmarkRead]:
    query = db.query(Benchmark)
    if sector:
        query = query.filter(Benchmark.sector == sector)
    return query.all()


@router.put("", response_model=BenchmarkRead)
def upsert_benchmark(payload: BenchmarkUpdate, db: Session = Depends(get_db)) -> BenchmarkRead:
    benchmark = (
        db.query(Benchmark)
        .filter(Benchmark.sector == payload.sector, Benchmark.key == payload.key)
        .first()
    )
    if benchmark:
        benchmark.value = payload.value
    else:
        benchmark = Benchmark(sector=payload.sector, key=payload.key, value=payload.value)
        db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark
