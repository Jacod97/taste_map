from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class RecommendationSession(Base):
    """추천 대화 세션"""
    __tablename__ = "recommendation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 세션 접근 토큰 (ID 추측 방지)
    access_token = Column(String(64), unique=True, index=True, nullable=False)

    # 대화 히스토리 (JSON 배열)
    messages = Column(JSON, default=list)

    # 수집된 컨텍스트 정보
    context = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RecommendationFeedback(Base):
    """추천 피드백"""
    __tablename__ = "recommendation_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("recommendation_sessions.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)

    is_helpful = Column(Integer)  # 1: 좋아요, -1: 별로예요, 0: 무응답

    created_at = Column(DateTime(timezone=True), server_default=func.now())
