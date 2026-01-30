from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from api.place.models import Place, Visibility
from api.place.schemas import PlaceCreate, PlaceUpdate, PlaceResponse
from api.review.models import Review


def _enrich_place_with_stats(db: Session, place: Place) -> PlaceResponse:
    """Place에 avg_rating, review_count 추가"""
    stats = db.query(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).filter(Review.place_id == place.id).first()

    return PlaceResponse(
        id=place.id,
        user_id=place.user_id,
        name=place.name,
        category=place.category,
        latitude=place.latitude,
        longitude=place.longitude,
        address=place.address,
        memo=place.memo,
        tags=place.tags,
        visited_at=place.visited_at,
        visibility=place.visibility,
        created_at=place.created_at,
        updated_at=place.updated_at,
        avg_rating=round(stats.avg_rating, 1) if stats.avg_rating else None,
        review_count=stats.review_count or 0
    )


def _enrich_places_with_stats(db: Session, places: list[Place]) -> list[PlaceResponse]:
    """여러 Place에 avg_rating, review_count 추가"""
    if not places:
        return []

    place_ids = [p.id for p in places]

    # 한 번의 쿼리로 모든 통계 조회
    stats = db.query(
        Review.place_id,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).filter(Review.place_id.in_(place_ids)).group_by(Review.place_id).all()

    stats_map = {s.place_id: (s.avg_rating, s.review_count) for s in stats}

    result = []
    for place in places:
        avg_rating, review_count = stats_map.get(place.id, (None, 0))
        result.append(PlaceResponse(
            id=place.id,
            user_id=place.user_id,
            name=place.name,
            category=place.category,
            latitude=place.latitude,
            longitude=place.longitude,
            address=place.address,
            memo=place.memo,
            tags=place.tags,
            visited_at=place.visited_at,
            visibility=place.visibility,
            created_at=place.created_at,
            updated_at=place.updated_at,
            avg_rating=round(avg_rating, 1) if avg_rating else None,
            review_count=review_count or 0
        ))
    return result


def create_place(db: Session, user_id: int, place_data: PlaceCreate) -> PlaceResponse:
    db_place = Place(
        user_id=user_id,
        **place_data.model_dump()
    )
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return _enrich_place_with_stats(db, db_place)


def get_place_by_id(db: Session, place_id: int) -> Place | None:
    return db.query(Place).filter(Place.id == place_id).first()


def get_place_response_by_id(db: Session, place_id: int) -> PlaceResponse | None:
    """Place 조회 + 통계 포함"""
    place = get_place_by_id(db, place_id)
    if not place:
        return None
    return _enrich_place_with_stats(db, place)


def get_user_places(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[PlaceResponse], int]:
    query = db.query(Place).filter(Place.user_id == user_id)
    total = query.count()
    places = query.offset(skip).limit(limit).all()
    return _enrich_places_with_stats(db, places), total


def get_places_in_bounds(
    db: Session,
    user_id: int,
    min_lat: float,
    max_lat: float,
    min_lng: float,
    max_lng: float,
    include_public: bool = False
) -> list[PlaceResponse]:
    """지도 영역 내 맛집 조회"""
    query = db.query(Place).filter(
        Place.latitude >= min_lat,
        Place.latitude <= max_lat,
        Place.longitude >= min_lng,
        Place.longitude <= max_lng
    )

    if include_public:
        query = query.filter(
            or_(Place.user_id == user_id, Place.visibility == Visibility.PUBLIC)
        )
    else:
        query = query.filter(Place.user_id == user_id)

    return _enrich_places_with_stats(db, query.all())


def get_places_nearby(
    db: Session,
    user_id: int,
    lat: float,
    lng: float,
    radius_km: float = 1.0,
    include_public: bool = False
) -> list[PlaceResponse]:
    """반경 내 맛집 조회 (간단한 거리 계산)"""
    # 대략적인 위도/경도 범위 계산 (1도 ≈ 111km)
    delta = radius_km / 111.0

    query = db.query(Place).filter(
        Place.latitude >= lat - delta,
        Place.latitude <= lat + delta,
        Place.longitude >= lng - delta,
        Place.longitude <= lng + delta
    )

    if include_public:
        query = query.filter(
            or_(Place.user_id == user_id, Place.visibility == Visibility.PUBLIC)
        )
    else:
        query = query.filter(Place.user_id == user_id)

    return _enrich_places_with_stats(db, query.all())


def search_places(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    category: str | None = None,
    min_rating: float | None = None,
    only_mine: bool = True,
    sort_by: str = "created_at",
    skip: int = 0,
    limit: int = 100
) -> tuple[list[PlaceResponse], int]:
    """맛집 검색/필터"""
    query = db.query(Place)

    if only_mine:
        query = query.filter(Place.user_id == user_id)
    else:
        query = query.filter(
            or_(Place.user_id == user_id, Place.visibility == Visibility.PUBLIC)
        )

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Place.name.ilike(keyword_filter),
                Place.memo.ilike(keyword_filter),
                Place.tags.ilike(keyword_filter)
            )
        )

    if category:
        query = query.filter(Place.category == category)

    # min_rating 필터: 서브쿼리로 평균 평점 필터링
    if min_rating is not None:
        subquery = db.query(
            Review.place_id,
            func.avg(Review.rating).label("avg_rating")
        ).group_by(Review.place_id).subquery()

        query = query.join(
            subquery, Place.id == subquery.c.place_id
        ).filter(subquery.c.avg_rating >= min_rating)

    # 정렬
    if sort_by == "created_at":
        query = query.order_by(Place.created_at.desc())
    elif sort_by == "name":
        query = query.order_by(Place.name)
    elif sort_by == "visited_at":
        query = query.order_by(Place.visited_at.desc())

    total = query.count()
    places = query.offset(skip).limit(limit).all()
    return _enrich_places_with_stats(db, places), total


def update_place(db: Session, place: Place, place_data: PlaceUpdate) -> PlaceResponse:
    update_data = place_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(place, field, value)
    db.commit()
    db.refresh(place)
    return _enrich_place_with_stats(db, place)


def delete_place(db: Session, place: Place) -> None:
    db.delete(place)
    db.commit()
