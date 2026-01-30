from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from api.review.models import RecommendationType


class ReviewCreate(BaseModel):
    place_id: int
    rating: float = Field(..., ge=1, le=5)
    content: Optional[str] = None
    recommendation: Optional[RecommendationType] = None


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1, le=5)
    content: Optional[str] = None
    recommendation: Optional[RecommendationType] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    place_id: int
    rating: float
    content: Optional[str]
    recommendation: Optional[RecommendationType]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewWithUserResponse(ReviewResponse):
    username: str


class PlaceReviewStats(BaseModel):
    place_id: int
    avg_rating: float
    review_count: int
