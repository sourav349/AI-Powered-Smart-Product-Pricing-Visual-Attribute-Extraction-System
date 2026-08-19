from pydantic import BaseModel, Field


class PricePredictionRequest(BaseModel):
    title: str = Field(..., min_length=2)
    category_name: str = Field(..., min_length=2)

    stars: float = Field(
        default=0,
        ge=0,
        le=5,
    )

    reviews: int = Field(
        default=0,
        ge=0,
    )

    bought_in_last_month: int = Field(
        default=0,
        ge=0,
    )

    is_best_seller: bool = False


class PricePredictionResponse(BaseModel):
    predicted_price: float
    cluster_id: int
    model_version: str
    device: str