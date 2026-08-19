from fastapi import APIRouter


router = APIRouter(
    prefix="/api/v1",
    tags=["Health"],
)


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AI Product Pricing API",
        "model_version": "final_clean_v1",
    }