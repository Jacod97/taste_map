from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api.config import get_settings
from api.database import get_db
from api.auth.models import User
from api.auth.schemas import UserCreate, UserResponse, Token, MessageResponse
from api.auth.service import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    authenticate_user,
    create_access_token,
    get_or_create_social_user,
    create_oauth_state,
    verify_and_consume_oauth_state,
)
from api.auth.dependencies import get_current_user
from api.auth.oauth import naver_oauth

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """회원가입"""
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다"
        )

    user = create_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """로그인 (username 필드에 이메일 입력)"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (클라이언트에서 토큰 삭제 필요)"""
    return MessageResponse(message="로그아웃되었습니다")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """내 정보 조회"""
    return current_user


# ==================== 네이버 OAuth ====================

@router.get("/naver")
def naver_login(db: Session = Depends(get_db)):
    """네이버 로그인 페이지로 리다이렉트"""
    state = create_oauth_state(db)
    authorization_url = naver_oauth.get_authorization_url(state)
    return RedirectResponse(url=authorization_url)


@router.get("/naver/callback", response_model=Token)
async def naver_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """네이버 로그인 콜백"""
    # state 검증 (1회용, 만료 체크 포함)
    if not verify_and_consume_oauth_state(db, state):
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 state입니다")

    # 액세스 토큰 발급
    access_token = await naver_oauth.get_access_token(code, state)

    # 사용자 정보 조회
    user_info = await naver_oauth.get_user_info(access_token)

    # 사용자 생성 또는 조회
    user = get_or_create_social_user(
        db,
        provider="naver",
        provider_id=user_info["id"],
        email=user_info.get("email"),
        username=user_info.get("nickname", "user"),
    )

    # JWT 토큰 발급
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    return Token(access_token=jwt_token, token_type="bearer")
