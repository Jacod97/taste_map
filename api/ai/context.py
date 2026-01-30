from sqlalchemy.orm import Session
from sqlalchemy import func

from api.place.models import Place
from api.review.models import Review


def build_places_context(db: Session, user_id: int) -> str:
    """사용자의 맛집 데이터를 컨텍스트 문자열로 변환"""
    places = db.query(Place).filter(Place.user_id == user_id).all()

    if not places:
        return "등록된 맛집이 없습니다."

    context_parts = []
    for place in places:
        # 평균 평점 조회
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.place_id == place.id
        ).scalar()

        # 리뷰 내용 조회
        reviews = db.query(Review).filter(Review.place_id == place.id).all()
        review_texts = [r.content for r in reviews if r.content]

        place_info = f"""
[맛집 ID: {place.id}]
- 이름: {place.name}
- 카테고리: {place.category.value if place.category else '기타'}
- 주소: {place.address or '미등록'}
- 위치: ({place.latitude}, {place.longitude})
- 태그: {place.tags or '없음'}
- 메모: {place.memo or '없음'}
- 평균 평점: {round(avg_rating, 1) if avg_rating else '평가 없음'}
- 리뷰: {'; '.join(review_texts) if review_texts else '리뷰 없음'}
"""
        context_parts.append(place_info)

    return "\n".join(context_parts)


def build_history_text(messages: list[dict], limit: int = 10) -> str:
    """대화 히스토리를 텍스트로 변환"""
    history_text = ""
    for msg in messages[-limit:]:
        role = "사용자" if msg["role"] == "user" else "AI"
        history_text += f"{role}: {msg['content']}\n"
    return history_text
