from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.prediction import router as prediction_router
from app.api.image_analysis import (
    router as image_analysis_router,
)


app = FastAPI(
    title="AI-Powered Smart Product Pricing API",
    description=(
        "Backend API for AI-based product price prediction "
        "and image attribute extraction."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    health_router
)

app.include_router(
    prediction_router
)

app.include_router(
    image_analysis_router
)


@app.get("/")
def root():
    return {
        "service": "AI-Powered Smart Product Pricing",
        "status": "running",
        "docs": "/docs",
    }