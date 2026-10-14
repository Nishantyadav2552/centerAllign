from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.core.config import settings, SCREENSHOTS_DIR, WORKSPACE_DIR
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.models import CompanyPolicy
from backend.app.services.pdf_generator import generate_all_demo_invoices
from backend.app.api import portal, tasks, approvals, finance, documents

# 1. Create DB tables on startup
Base.metadata.create_all(bind=engine)

# 2. Seed initial company policies
def seed_initial_policies():
    db = SessionLocal()
    try:
        if not db.query(CompanyPolicy).filter(CompanyPolicy.key == "financial_approval").first():
            pol1 = CompanyPolicy(
                id="pol_fin_01",
                key="financial_approval",
                title="Consequential Financial Action Gate",
                description="Creation or modification of vendor invoices in internal finance databases requires human supervisor authorization.",
                rule_value="REQUIRES_APPROVAL_ALWAYS"
            )
            pol2 = CompanyPolicy(
                id="pol_due_02",
                key="due_date_resolution",
                title="Ambiguous Due Date Handling",
                description="If an invoice contains ambiguous or missing payment terms, the operator must pause and request human supervisor clarification instead of fabricating data.",
                rule_value="PAUSE_AND_CLARIFY"
            )
            db.add_all([pol1, pol2])
            db.commit()
    finally:
        db.close()

seed_initial_policies()
generate_all_demo_invoices()

# 3. FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CentrAlign Operator: Autonomous AI Employee for Business Task Execution"
)

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Static mounts
if SCREENSHOTS_DIR.exists():
    app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")

# 6. Include Routers
app.include_router(portal.router)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(approvals.router, prefix=settings.API_V1_STR)
app.include_router(finance.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)

@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "llm_provider": settings.LLM_PROVIDER
    }

FRONTEND_DIST = WORKSPACE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/", tags=["System"])
    def root():
        return {
            "message": "CentrAlign Operator Backend is running.",
            "docs_url": "/docs",
            "portal_url": "/portal",
            "health_url": "/api/health"
        }
