from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from api.database import Base


class Category(str, enum.Enum):
    KOREAN = "korean"        # 한식
    JAPANESE = "japanese"    # 일식
    CHINESE = "chinese"      # 중식
    WESTERN = "western"      # 양식
    CAFE = "cafe"            # 카페
    BAR = "bar"              # 술집
    FASTFOOD = "fastfood"    # 패스트푸드
    DESSERT = "dessert"      # 디저트
    OTHER = "other"          # 기타


class Visibility(str, enum.Enum):
    PRIVATE = "private"      # 나만 보기
    PUBLIC = "public"        # 공개


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(200), nullable=False, index=True)
    category = Column(SQLEnum(Category), default=Category.OTHER)

    # 위치 정보
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500))

    # 추가 정보
    memo = Column(Text)
    tags = Column(String(500))  # 쉼표로 구분된 태그
    visited_at = Column(DateTime(timezone=True))

    # 공개 범위
    visibility = Column(SQLEnum(Visibility), default=Visibility.PUBLIC)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="places")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")
