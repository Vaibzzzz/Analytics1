from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from KPI.KPI_Dashboard import router as dashboard_router
from API.financial_analysis_service import router as financial_analysis_router
from API.operational_ef import router as operational_efficiency_router
from API.DemoGraphic import router as demographic_router  # FIX: this is already the router

app = FastAPI(title="A360 Prototype Dashboard API")

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTES ────────────────────────────────────────────────────────────
app.include_router(dashboard_router, prefix="/api")
app.include_router(financial_analysis_router, prefix="/api")
app.include_router(operational_efficiency_router, prefix="/api")
app.include_router(demographic_router, prefix="/api")  
