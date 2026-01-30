import google.generativeai as genai

from api.config import get_settings

settings = get_settings()

# Gemini 설정
genai.configure(api_key=settings.GEMINI_API_KEY)

# 모델 인스턴스
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def generate_response(prompt: str) -> str:
    """Gemini API 호출"""
    response = gemini_model.generate_content(prompt)
    return response.text
