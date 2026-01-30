from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.auth.models import User
from api.auth.dependencies import get_current_user
from api.place.models import Category, Visibility
from api.place.schemas import PlaceCreate, PlaceUpdate, PlaceResponse, PlaceListResponse
from api.place import service

router = APIRouter(prefix="/places", tags=["places"])


@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_place(
    place_data: PlaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집 등록"""
    place = service.create_place(db, current_user.id, place_data)
    return place


@router.get("", response_model=PlaceListResponse)
def get_my_places(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """내 맛집 목록 조회"""
    places, total = service.get_user_places(db, current_user.id, skip, limit)
    return PlaceListResponse(places=places, total=total)


@router.get("/bounds", response_model=list[PlaceResponse])
def get_places_in_bounds(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lng: float = Query(..., ge=-180, le=180),
    max_lng: float = Query(..., ge=-180, le=180),
    include_public: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """지도 영역 내 맛집 조회"""
    places = service.get_places_in_bounds(
        db, current_user.id, min_lat, max_lat, min_lng, max_lng, include_public
    )
    return places


@router.get("/nearby", response_model=list[PlaceResponse])
def get_nearby_places(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(1.0, ge=0.1, le=50),
    include_public: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """내 위치 기반 주변 맛집 조회"""
    places = service.get_places_nearby(
        db, current_user.id, lat, lng, radius_km, include_public
    )
    return places


@router.get("/search", response_model=PlaceListResponse)
def search_places(
    keyword: str | None = Query(None),
    category: Category | None = Query(None),
    min_rating: float | None = Query(None, ge=1, le=5),
    only_mine: bool = Query(True),
    sort_by: str = Query("created_at", regex="^(created_at|name|visited_at)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집 검색/필터"""
    places, total = service.search_places(
        db, current_user.id, keyword, category, min_rating, only_mine, sort_by, skip, limit
    )
    return PlaceListResponse(places=places, total=total)


@router.get("/{place_id}", response_model=PlaceResponse)
def get_place(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집 상세 조회"""
    place = service.get_place_by_id(db, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="맛집을 찾을 수 없습니다")

    # 권한 확인: 본인 것이거나 공개된 것만 조회 가능
    if place.user_id != current_user.id and place.visibility != Visibility.PUBLIC:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    return service.get_place_response_by_id(db, place_id)


@router.put("/{place_id}", response_model=PlaceResponse)
def update_place(
    place_id: int,
    place_data: PlaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집 수정"""
    place = service.get_place_by_id(db, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="맛집을 찾을 수 없습니다")

    if place.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

    updated_place = service.update_place(db, place, place_data)
    return updated_place


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집 삭제"""
    place = service.get_place_by_id(db, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="맛집을 찾을 수 없습니다")

    if place.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

    service.delete_place(db, place)
