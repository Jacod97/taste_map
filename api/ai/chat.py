import json

from sqlalchemy.orm import Session
from sqlalchemy import func

from api.place.models import Place
from api.review.models import Review
from api.recommend.schemas import RecommendResponse, RecommendedPlace
from api.ai.model import generate_response
from api.ai.prompts import build_recommendation_prompt
from api.ai.context import build_places_context, build_history_text


def parse_ai_response(response_text: str) -> dict:
    """AI 응답 파싱"""
    try:
        # 코드 블록 제거
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except Exception:
        return {
            "message": "죄송합니다. 추천을 처리하는 중 오류가 발생했습니다. 다시 시도해주세요.",
            "is_asking": False,
            "place_ids": [],
            "reasons": {}
        }


def get_place_with_rating(db: Session, place_id: int) -> tuple[Place | None, float | None]:
    """맛집과 평균 평점 조회"""
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        return None, None

    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.place_id == place.id
    ).scalar()

    return place, round(avg_rating, 1) if avg_rating else None


def generate_recommendation(
    db: Session,
    user_id: int,
    user_message: str,
    messages_history: list[dict],
    latitude: float | None = None,
    longitude: float | None = None
) -> tuple[str, bool, list[RecommendedPlace]]:
    """AI 추천 생성

    Returns:
        tuple: (AI 응답 메시지, 추가 질문 중인지, 추천 맛집 목록)
    """
    # 컨텍스트 빌드
    places_context = build_places_context(db, user_id)
    history_text = build_history_text(messages_history)

    location_info = ""
    if latitude and longitude:
        location_info = f"\n현재 사용자 위치: ({latitude}, {longitude})"

    # 프롬프트 생성
    prompt = build_recommendation_prompt(
        places_context=places_context,
        history_text=history_text,
        user_message=user_message,
        location_info=location_info
    )

    # AI 호출
    response_text = generate_response(prompt)
    result = parse_ai_response(response_text)

    # 추천 맛집 정보 조회
    recommended_places = []
    for place_id in result.get("place_ids", []):
        place, avg_rating = get_place_with_rating(db, place_id)
        if place:
            recommended_places.append(RecommendedPlace(
                id=place.id,
                name=place.name,
                category=place.category.value if place.category else "other",
                address=place.address,
                latitude=place.latitude,
                longitude=place.longitude,
                avg_rating=avg_rating,
                reason=result.get("reasons", {}).get(str(place_id), "")
            ))

    return (
        result["message"],
        result.get("is_asking", False),
        recommended_places
    )
