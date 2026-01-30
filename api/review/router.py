from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.auth.models import User
from api.auth.dependencies import get_current_user
from api.place.service import get_place_by_id
from api.place.models import Place, Visibility
from api.review.schemas import ReviewCreate, ReviewUpdate, ReviewResponse, PlaceReviewStats
from api.review import service

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _check_place_access(place: Place | None, user_id: int) -> Place:
    """맛집 존재 및 접근 권한 확인"""
    if not place:
        raise HTTPException(status_code=404, detail="맛집을 찾을 수 없습니다")

    if place.user_id != user_id and place.visibility != Visibility.PUBLIC:
        raise HTTPException(status_code=403, detail="비공개 맛집에는 접근할 수 없습니다")

    return place


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """리뷰 작성"""
    # 맛집 존재 및 접근 권한 확인
    place = get_place_by_id(db, review_data.place_id)
    _check_place_access(place, current_user.id)

    # 중복 리뷰 확인
    if service.check_user_reviewed(db, current_user.id, review_data.place_id):
        raise HTTPException(status_code=400, detail="이미 리뷰를 작성한 맛집입니다")

    review = service.create_review(db, current_user.id, review_data)
    return review


@router.get("/place/{place_id}", response_model=list[ReviewResponse])
def get_place_reviews(
    place_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집의 리뷰 목록 조회"""
    # 맛집 존재 및 접근 권한 확인
    place = get_place_by_id(db, place_id)
    _check_place_access(place, current_user.id)

    reviews, _ = service.get_reviews_by_place(db, place_id, skip, limit)
    return reviews


@router.get("/place/{place_id}/stats", response_model=PlaceReviewStats)
def get_place_review_stats(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """맛집의 평균 평점/리뷰 수 조회"""
    # 맛집 존재 및 접근 권한 확인
    place = get_place_by_id(db, place_id)
    _check_place_access(place, current_user.id)

    return service.get_place_stats(db, place_id)


@router.get("/my", response_model=list[ReviewResponse])
def get_my_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """내 리뷰 목록 조회"""
    reviews, _ = service.get_reviews_by_user(db, current_user.id, skip, limit)
    return reviews


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """리뷰 상세 조회"""
    review = service.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")

    # 리뷰가 달린 맛집의 접근 권한 확인
    place = get_place_by_id(db, review.place_id)
    _check_place_access(place, current_user.id)

    return review


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """리뷰 수정"""
    review = service.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

    updated_review = service.update_review(db, review, review_data)
    return updated_review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """리뷰 삭제"""
    review = service.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다")

    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

    service.delete_review(db, review)
