import asyncio
import secrets
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.recommend.models import RecommendationSession, RecommendationFeedback
from api.recommend.schemas import RecommendRequest, RecommendResponse
from api.place.models import Place, Visibility
from api.ai.chat import generate_recommendation

logger = logging.getLogger(__name__)


def create_session(db: Session, user_id: int) -> RecommendationSession:
    """새 추천 세션 생성"""
    session = RecommendationSession(
        user_id=user_id,
        access_token=secrets.token_urlsafe(48),
        messages=[],
        context={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_token(db: Session, access_token: str, user_id: int) -> RecommendationSession | None:
    """토큰으로 세션 조회 (소유자 검증 포함)"""
    return db.query(RecommendationSession).filter(
        RecommendationSession.access_token == access_token,
        RecommendationSession.user_id == user_id
    ).first()


def update_session_messages(
    db: Session,
    session: RecommendationSession,
    user_message: str,
    assistant_message: str
):
    """세션 메시지 업데이트"""
    messages = list(session.messages or [])
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": assistant_message})
    session.messages = messages
    db.commit()


async def get_recommendation(
    db: Session,
    user_id: int,
    request: RecommendRequest
) -> RecommendResponse:
    """AI 추천 요청 처리"""
    # 세션 처리
    if request.session_token:
        session = get_session_by_token(db, request.session_token, user_id)
        if not session:
            session = create_session(db, user_id)
    else:
        session = create_session(db, user_id)

    # AI 추천 생성 (동기 함수를 비동기로 실행 + 예외 처리)
    try:
        message, is_asking, recommended_places = await asyncio.to_thread(
            generate_recommendation,
            db=db,
            user_id=user_id,
            user_message=request.message,
            messages_history=session.messages or [],
            latitude=request.latitude,
            longitude=request.longitude
        )
    except Exception as e:
        logger.error(f"AI 추천 생성 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI 추천 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
        )

    # 세션 메시지 업데이트
    update_session_messages(db, session, request.message, message)

    return RecommendResponse(
        session_token=session.access_token,
        message=message,
        is_asking=is_asking,
        recommended_places=recommended_places
    )


def save_feedback(
    db: Session,
    user_id: int,
    session_token: str,
    place_id: int,
    is_helpful: int
):
    """추천 피드백 저장"""
    # 세션 소유자 검증
    session = get_session_by_token(db, session_token, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 맛집 접근 권한 검증 (본인 것이거나 공개)
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="맛집을 찾을 수 없습니다")

    if place.user_id != user_id and place.visibility != Visibility.PUBLIC:
        raise HTTPException(status_code=403, detail="접근 권한이 없는 맛집입니다")

    feedback = RecommendationFeedback(
        user_id=user_id,
        session_id=session.id,
        place_id=place_id,
        is_helpful=is_helpful
    )
    db.add(feedback)
    db.commit()
