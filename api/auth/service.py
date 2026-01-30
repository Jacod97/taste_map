from datetime import datetime, timedelta, timezone
import secrets

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.config import get_settings
from api.auth.models import User, OAuthState
from api.auth.schemas import UserCreate

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not user.hashed_password:  # 소셜 로그인 사용자
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_or_create_social_user(
    db: Session,
    provider: str,
    provider_id: str,
    email: str | None,
    username: str
) -> User:
    """소셜 로그인 사용자 조회 또는 생성"""
    # provider_id로 기존 사용자 찾기
    user = db.query(User).filter(
        User.provider == provider,
        User.provider_id == provider_id
    ).first()

    if user:
        return user

    # 이메일로 기존 사용자 찾기 (계정 연동)
    if email:
        user = get_user_by_email(db, email)
        if user:
            user.provider = provider
            user.provider_id = provider_id
            db.commit()
            db.refresh(user)
            return user

    # 새 사용자 생성 (난수 접미사로 race condition 방지)
    max_retries = 5
    for _ in range(max_retries):
        random_suffix = secrets.token_hex(4)
        unique_username = f"{username}_{random_suffix}"

        db_user = User(
            email=email or f"{provider}_{provider_id}@tastemap.local",
            username=unique_username,
            provider=provider,
            provider_id=provider_id,
        )
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            continue

    raise Exception("사용자 생성에 실패했습니다. 잠시 후 다시 시도해주세요.")


# ==================== OAuth State 관리 ====================

def create_oauth_state(db: Session) -> str:
    """OAuth state 생성 및 DB 저장"""
    # 만료된 state 정리
    expire_time = datetime.now(timezone.utc) - timedelta(minutes=settings.OAUTH_STATE_EXPIRE_MINUTES)
    db.query(OAuthState).filter(OAuthState.created_at < expire_time).delete()
    db.commit()

    # 새 state 생성
    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(state=state)
    db.add(oauth_state)
    db.commit()
    return state


def verify_and_consume_oauth_state(db: Session, state: str) -> bool:
    """OAuth state 검증 및 삭제 (1회용)"""
    expire_time = datetime.now(timezone.utc) - timedelta(minutes=settings.OAUTH_STATE_EXPIRE_MINUTES)

    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.created_at >= expire_time
    ).first()

    if not oauth_state:
        return False

    db.delete(oauth_state)
    db.commit()
    return True
