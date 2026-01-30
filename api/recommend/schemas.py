from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class RecommendRequest(BaseModel):
    message: str
    session_token: Optional[str] = None  # 기존 세션 연결용 토큰
    # 선택적 컨텍스트
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RecommendedPlace(BaseModel):
    id: int
    name: str
    category: str
    address: Optional[str]
    latitude: float
    longitude: float
    avg_rating: Optional[float]
    reason: str  # 추천 이유


class RecommendResponse(BaseModel):
    session_token: str  # 세션 접근 토큰
    message: str  # AI 응답 메시지
    is_asking: bool  # 추가 질문 중인지
    recommended_places: list[RecommendedPlace]  # 추천된 맛집 목록


class FeedbackRequest(BaseModel):
    session_token: str  # 세션 토큰으로 검증
    place_id: int
    is_helpful: int  # 1: 좋아요, -1: 별로예요


class SessionResponse(BaseModel):
    session_token: str
    messages: list[ChatMessage]
    created_at: datetime
