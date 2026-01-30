from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import Base, engine
from api.auth.router import router as auth_router
from api.place.router import router as place_router
from api.review.router import router as review_router
from api.recommend.router import router as recommend_router

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Taste Map API",
    description="맛집 지도 API - 내가 방문한 맛집을 기록하고 AI 추천을 받아보세요",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(place_router)
app.include_router(review_router)
app.include_router(recommend_router)


@app.get("/")
def root():
    return {"message": "Taste Map API", "docs": "/docs"}
