from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from api.place.models import Category, Visibility


class PlaceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    category: Category = Category.OTHER
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    memo: Optional[str] = None
    tags: Optional[str] = None
    visited_at: Optional[datetime] = None
    visibility: Visibility = Visibility.PUBLIC


class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    category: Optional[Category] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    memo: Optional[str] = None
    tags: Optional[str] = None
    visited_at: Optional[datetime] = None
    visibility: Optional[Visibility] = None


class PlaceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    category: Category
    latitude: float
    longitude: float
    address: Optional[str]
    memo: Optional[str]
    tags: Optional[str]
    visited_at: Optional[datetime]
    visibility: Visibility
    created_at: datetime
    updated_at: Optional[datetime]

    # 집계 정보
    avg_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class PlaceListResponse(BaseModel):
    places: list[PlaceResponse]
    total: int
