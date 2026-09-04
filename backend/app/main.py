import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, func as sql_func

from app.database import get_db
from app import models  # noqa: F401 — ensure all models are registered
from app.models.inspection import Inspection
from app.models.compliance_result import ComplianceResult
from app.models.user import User
from app.routers import inspection_upload
from app.routers import ocr
from app.routers import extraction
from app.routers import compliance
from app.routers import auth
from app.routers import inspections
from app.routers import dashboard
from app.routers import reports

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LegalMetriX API",
    description="Packaged Commodity Compliance & Inspection Support System",
    version="0.2.0",
)

# CORS — allow the Vite dev server (localhost:5173) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(inspection_upload.router)
app.include_router(ocr.router)
app.include_router(extraction.router)
app.include_router(compliance.router)
app.include_router(inspections.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "name": "LegalMetriX",
        "message": "Packaged Commodity Compliance & Inspection Support",
        "version": "0.2.0",
    }


@app.get("/api/public/stats")
def public_stats(db: Session = Depends(get_db)):
    """Public aggregate statistics for the landing page. No auth required."""
    try:
        total_inspections = db.query(sql_func.count(Inspection.id)).scalar() or 0
        total_inspectors = db.query(sql_func.count(User.id)).filter(
            User.role == "INSPECTOR"
        ).scalar() or 0

        compliant = db.query(sql_func.count(ComplianceResult.id)).filter(
            ComplianceResult.overall_status == "COMPLIANT"
        ).scalar() or 0
        non_compliant = db.query(sql_func.count(ComplianceResult.id)).filter(
            ComplianceResult.overall_status == "NON_COMPLIANT"
        ).scalar() or 0
        review_required = db.query(sql_func.count(ComplianceResult.id)).filter(
            ComplianceResult.overall_status == "REVIEW_REQUIRED"
        ).scalar() or 0
        incomplete = total_inspections - (compliant + non_compliant + review_required)
        if incomplete < 0:
            incomplete = 0

        return {
            "total_inspections": total_inspections,
            "total_inspectors": total_inspectors,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "review_required": review_required,
            "incomplete": incomplete,
        }
    except Exception as exc:
        logger.exception("Failed to load public stats")
        return {
            "total_inspections": 0,
            "total_inspectors": 0,
            "compliant": 0,
            "non_compliant": 0,
            "review_required": 0,
            "incomplete": 0,
        }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "healthy",
        "service": "LegalMetriX API",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
