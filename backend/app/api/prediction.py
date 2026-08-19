from fastapi import APIRouter, HTTPException

from app.schemas.prediction import (
    PricePredictionRequest,
    PricePredictionResponse,
)

from app.services.price_predictor import (
    predict_product_price,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Price Prediction"],
)


@router.post(
    "/predict",
    response_model=PricePredictionResponse,
)
def predict_price(
    request: PricePredictionRequest,
):
    try:
        result = predict_product_price(
            title=request.title,
            category_name=request.category_name,
            stars=request.stars,
            reviews=request.reviews,
            bought_in_last_month=request.bought_in_last_month,
            is_best_seller=request.is_best_seller,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {error}",
        )