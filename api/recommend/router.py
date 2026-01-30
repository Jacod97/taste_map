from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.auth.models import User
from api.auth.dependencies import get_current_user
from api.recommend.schemas import (
    RecommendRequest,
    RecommendResponse,
    FeedbackRequest,
    SessionResponse,
    ChatMessage,
)
from api.recommend import service

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("", response_model=RecommendResponse)
async def get_recommendation(
    request: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 맛집 추천 요청

    자연어로 맛집 추천을 요청합니다.
    """
    response = await service.get_recommendation(db, current_user.id, request)
    return response


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """추천 피드백 제출

    추천이 도움이 되었는지 피드백을 제출합니다.
    is_helpful: 1 (좋아요), -1 (별로예요)
    """
    service.save_feedback(
        db,
        current_user.id,
        request.session_token,
        request.place_id,
        request.is_helpful
    )


@router.get("/sessions/{session_token}", response_model=SessionResponse)
def get_session(
    session_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """추천 세션 대화 내역 조회"""
    session = service.get_session_by_token(db, session_token, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    messages = [
        ChatMessage(role=msg["role"], content=msg["content"])
        for msg in (session.messages or [])
    ]

    return SessionResponse(
        session_token=session.access_token,
        messages=messages,
        created_at=session.created_at
    )
