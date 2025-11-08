# Sales Funnel

Sales Funnel is a FastAPI-based platform that orchestrates predictable revenue funnels across digital, offline, and hybrid motions. It exposes a REST API capable of onboarding funis, configuring capacity and channel data, simulating scenarios, and generating automated recommendations for revenue attainment.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

After the server is running you can hit `POST /api/v1/auth/seed` once to create a default admin user (`admin@salesfunnel.io` / `admin`) bound to the default workspace. From there authenticate via `POST /api/v1/auth/login` and use the token for all subsequent requests.

## Key API flows

1. **Create a funnel** – `POST /api/v1/funnels` with the onboarding payload (mode, submode, metrics, capacity, channels).
2. **Update metrics, capacity, and channels** – dedicated endpoints keep the funnel current.
3. **Create scenarios** – `POST /api/v1/funnels/{id}/scenarios` to store override bundles for simulation.
4. **Run the calculator** – `POST /api/v1/scenarios/{id}/calculate` executes the strategy-specific calculator, persists the results, and returns KPIs, gap analysis, bottleneck, and recommended actions.
5. **Manage benchmarks** – `GET /api/v1/benchmarks` and `PUT /api/v1/benchmarks` maintain sector baselines that power the rule engine.

All business rules described in the product blueprint are encoded in the calculator strategies and advisor engine, allowing the API to answer "Bateremos a meta? Onde está o gargalo? O que fazer agora?" in a single call.
