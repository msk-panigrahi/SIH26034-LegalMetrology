from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="LegalMetriX API",
    description="Packaged Commodity Compliance & Inspection Support System",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "LegalMetriX",
        "message": "Packaged Commodity Compliance & Inspection Support",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LegalMetriX API",
        "timestamp": datetime.utcnow().isoformat(),
    }
