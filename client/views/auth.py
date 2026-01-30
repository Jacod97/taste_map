import streamlit as st
from client.api import api_client


def show_auth_page():
    st.title("🍽️ TasteMap")
    st.write("나만의 맛집 지도를 만들어보세요!")

    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        show_login_form()

    with tab2:
        show_signup_form()


def show_login_form():
    with st.form("login_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 입력해주세요.")
                return

            try:
                result = api_client.login(email, password)
                token = result["access_token"]
                api_client.set_token(token)
                st.session_state.token = token

                user = api_client.get_me()
                st.session_state.user = user

                st.success("로그인 성공!")
                st.rerun()
            except Exception as e:
                st.error(f"로그인 실패: {e}")


def show_signup_form():
    with st.form("signup_form"):
        email = st.text_input("이메일")
        username = st.text_input("사용자명")
        password = st.text_input("비밀번호", type="password")
        password_confirm = st.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("회원가입", use_container_width=True)

        if submitted:
            if not email or not username or not password:
                st.error("모든 필드를 입력해주세요.")
                return

            if password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
                return

            try:
                api_client.signup(email, username, password)
                st.success("회원가입 성공! 로그인해주세요.")
            except Exception as e:
                st.error(f"회원가입 실패: {e}")
