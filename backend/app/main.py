from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine
from .models import Base
from .routers import auth, benchmarks, funnels, scenarios
from .startup import ensure_bootstrap_data

Base.metadata.create_all(bind=engine)
ensure_bootstrap_data()

app = FastAPI(title="Sales Funnel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(funnels.router, prefix="/api/v1")
app.include_router(scenarios.router, prefix="/api/v1")
app.include_router(benchmarks.router, prefix="/api/v1")
