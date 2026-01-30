import httpx
from typing import Optional

API_BASE_URL = "http://localhost:8000"


class APIClient:
    def __init__(self):
        self.token: Optional[str] = None

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def set_token(self, token: str):
        self.token = token

    def clear_token(self):
        self.token = None

    # ==================== Auth ====================

    def signup(self, email: str, username: str, password: str) -> dict:
        response = httpx.post(
            f"{API_BASE_URL}/auth/signup",
            json={"email": email, "username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> dict:
        response = httpx.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def get_me(self) -> dict:
        response = httpx.get(
            f"{API_BASE_URL}/auth/me",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    # ==================== Places ====================

    def get_my_places(self, skip: int = 0, limit: int = 100) -> dict:
        response = httpx.get(
            f"{API_BASE_URL}/places",
            headers=self._headers(),
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def create_place(self, data: dict) -> dict:
        response = httpx.post(
            f"{API_BASE_URL}/places",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_place(self, place_id: int) -> dict:
        response = httpx.get(
            f"{API_BASE_URL}/places/{place_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def update_place(self, place_id: int, data: dict) -> dict:
        response = httpx.put(
            f"{API_BASE_URL}/places/{place_id}",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_place(self, place_id: int):
        response = httpx.delete(
            f"{API_BASE_URL}/places/{place_id}",
            headers=self._headers()
        )
        response.raise_for_status()

    def search_places(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        only_mine: bool = True
    ) -> dict:
        params = {"only_mine": only_mine}
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category
        if min_rating:
            params["min_rating"] = min_rating

        response = httpx.get(
            f"{API_BASE_URL}/places/search",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    # ==================== Reviews ====================

    def get_place_reviews(self, place_id: int) -> list:
        response = httpx.get(
            f"{API_BASE_URL}/reviews/place/{place_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def create_review(self, place_id: int, rating: float, content: str, recommendation: Optional[str] = None) -> dict:
        data = {"place_id": place_id, "rating": rating, "content": content}
        if recommendation:
            data["recommendation"] = recommendation

        response = httpx.post(
            f"{API_BASE_URL}/reviews",
            headers=self._headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_my_reviews(self) -> list:
        response = httpx.get(
            f"{API_BASE_URL}/reviews/my",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def delete_review(self, review_id: int):
        response = httpx.delete(
            f"{API_BASE_URL}/reviews/{review_id}",
            headers=self._headers()
        )
        response.raise_for_status()

    # ==================== Recommend ====================

    def get_recommendation(
        self,
        message: str,
        session_token: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> dict:
        data = {"message": message}
        if session_token:
            data["session_token"] = session_token
        if latitude:
            data["latitude"] = latitude
        if longitude:
            data["longitude"] = longitude

        response = httpx.post(
            f"{API_BASE_URL}/recommend",
            headers=self._headers(),
            json=data,
            timeout=60.0  # AI 응답 대기
        )
        response.raise_for_status()
        return response.json()

    def submit_feedback(self, session_token: str, place_id: int, is_helpful: int):
        response = httpx.post(
            f"{API_BASE_URL}/recommend/feedback",
            headers=self._headers(),
            json={
                "session_token": session_token,
                "place_id": place_id,
                "is_helpful": is_helpful
            }
        )
        response.raise_for_status()


# 싱글톤 인스턴스
api_client = APIClient()
