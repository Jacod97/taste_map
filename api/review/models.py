from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from api.database import Base


class RecommendationType(str, enum.Enum):
    HIGHLY_RECOMMEND = "highly_recommend"  # 강추
    RECOMMEND = "recommend"                 # 추천
    REVISIT = "revisit"                    # 재방문 의사
    NOT_RECOMMEND = "not_recommend"        # 비추


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)

    # 평가 정보
    rating = Column(Float, nullable=False)  # 1~5점
    content = Column(Text)  # 리뷰 텍스트
    recommendation = Column(SQLEnum(RecommendationType))  # 추천 플래그

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="reviews")
    place = relationship("Place", back_populates="reviews")
