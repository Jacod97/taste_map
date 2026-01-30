from sqlalchemy.orm import Session
from sqlalchemy import func

from api.review.models import Review
from api.review.schemas import ReviewCreate, ReviewUpdate


def create_review(db: Session, user_id: int, review_data: ReviewCreate) -> Review:
    db_review = Review(
        user_id=user_id,
        **review_data.model_dump()
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def get_review_by_id(db: Session, review_id: int) -> Review | None:
    return db.query(Review).filter(Review.id == review_id).first()


def get_reviews_by_place(
    db: Session,
    place_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Review], int]:
    query = db.query(Review).filter(Review.place_id == place_id)
    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews, total


def get_reviews_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Review], int]:
    query = db.query(Review).filter(Review.user_id == user_id)
    total = query.count()
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews, total


def get_place_stats(db: Session, place_id: int) -> dict:
    """맛집의 평균 평점과 리뷰 수 조회"""
    result = db.query(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).filter(Review.place_id == place_id).first()

    return {
        "place_id": place_id,
        "avg_rating": round(result.avg_rating, 1) if result.avg_rating else 0,
        "review_count": result.review_count or 0
    }


def update_review(db: Session, review: Review, review_data: ReviewUpdate) -> Review:
    update_data = review_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()


def check_user_reviewed(db: Session, user_id: int, place_id: int) -> bool:
    """사용자가 해당 맛집에 리뷰를 작성했는지 확인"""
    return db.query(Review).filter(
        Review.user_id == user_id,
        Review.place_id == place_id
    ).first() is not None
