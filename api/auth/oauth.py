import httpx
from fastapi import HTTPException

from api.config import get_settings

settings = get_settings()


class NaverOAuth:
    AUTHORIZE_URL = "https://nid.naver.com/oauth2.0/authorize"
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    PROFILE_URL = "https://openapi.naver.com/v1/nid/me"

    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.redirect_uri = settings.NAVER_REDIRECT_URI

    def get_authorization_url(self, state: str) -> str:
        """네이버 로그인 페이지 URL 생성"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}"

    async def get_access_token(self, code: str, state: str) -> str:
        """인가 코드로 액세스 토큰 발급"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "state": state,
                },
            )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="네이버 토큰 발급 실패")

        data = response.json()
        if "access_token" not in data:
            raise HTTPException(status_code=400, detail="네이버 토큰 발급 실패")

        return data["access_token"]

    async def get_user_info(self, access_token: str) -> dict:
        """액세스 토큰으로 사용자 정보 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="네이버 사용자 정보 조회 실패")

        data = response.json()
        if data.get("resultcode") != "00":
            raise HTTPException(status_code=400, detail="네이버 사용자 정보 조회 실패")

        user_info = data.get("response", {})
        return {
            "id": user_info.get("id"),
            "email": user_info.get("email"),
            "nickname": user_info.get("nickname") or user_info.get("name"),
        }


naver_oauth = NaverOAuth()
