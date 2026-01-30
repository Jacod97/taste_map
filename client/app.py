import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="TasteMap",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "recommend_session_token" not in st.session_state:
    st.session_state.recommend_session_token = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_place" not in st.session_state:
    st.session_state.selected_place = None
if "map_center" not in st.session_state:
    st.session_state.map_center = [37.5665, 126.9780]  # 서울 기본
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 13


def main():
    if st.session_state.token:
        show_main_app()
    else:
        show_login_page()


def show_login_page():
    from client.views import auth
    auth.show_auth_page()


def show_main_app():
    from client.api import api_client

    # 사이드바
    with st.sidebar:
        st.title("🍽️ TasteMap")
        st.write(f"👋 {st.session_state.user['username']}님")

        if st.button("로그아웃", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            api_client.clear_token()
            st.rerun()

        st.divider()

        menu = st.radio(
            "메뉴",
            ["🗺️ 지도", "➕ 맛집 등록", "🤖 AI 추천"],
            label_visibility="collapsed"
        )

    # 메인 컨텐츠
    if menu == "🗺️ 지도":
        from client.views import map_view
        map_view.show_map_view()
    elif menu == "➕ 맛집 등록":
        from client.views import places
        places.show_add_place()
    elif menu == "🤖 AI 추천":
        from client.views import recommend
        recommend.show_recommend()


if __name__ == "__main__":
    main()
