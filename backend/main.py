from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from API.API_Dashboard import router as dashboard_router
from API.financial_analysis_service import router as financial_analysis_router
from API.operational_ef import router as operational_efficiency_router
from API.DemoGraphic import router as demographic_router
from API.risk_and_fraud_management import router as risk_and_fraud_router
from API.customer_insight import router as customer_insight_router
from API.report import router as report_router

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
app.include_router(risk_and_fraud_router, prefix="/api")
app.include_router(customer_insight_router, prefix="/api")
app.include_router(report_router, prefix="/api")