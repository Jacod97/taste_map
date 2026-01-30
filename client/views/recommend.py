import streamlit as st
from client.api import api_client


def show_recommend():
    st.title("🤖 AI 맛집 추천")
    st.caption("자연어로 맛집 추천을 요청해보세요!")

    # 채팅 히스토리 표시
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

            # 추천된 맛집 표시
            if msg.get("places"):
                show_recommended_places(msg["places"], msg.get("session_token"))

    # 새 대화 시작 버튼
    if st.session_state.chat_history:
        if st.button("🔄 새 대화 시작"):
            st.session_state.chat_history = []
            st.session_state.recommend_session_token = None
            st.rerun()

    # 채팅 입력
    if prompt := st.chat_input("예: 오늘 점심 뭐 먹을까?"):
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        # AI 응답 받기
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                try:
                    response = api_client.get_recommendation(
                        message=prompt,
                        session_token=st.session_state.recommend_session_token
                    )

                    # 세션 토큰 저장
                    st.session_state.recommend_session_token = response["session_token"]

                    # AI 응답 표시
                    st.write(response["message"])

                    # 추천 맛집 표시
                    if response["recommended_places"]:
                        show_recommended_places(
                            response["recommended_places"],
                            response["session_token"]
                        )

                    # 히스토리에 추가
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response["message"],
                        "places": response["recommended_places"],
                        "session_token": response["session_token"]
                    })

                except Exception as e:
                    error_msg = f"추천을 받는 중 오류가 발생했습니다: {e}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # 예시 질문
    if not st.session_state.chat_history:
        st.divider()
        st.write("**이런 것들을 물어보세요:**")

        examples = [
            "오늘 점심 뭐 먹을까?",
            "매운 음식 땡기는데 추천해줘",
            "혼밥하기 좋은 곳 있어?",
            "데이트하기 좋은 분위기 있는 곳",
            "카페 추천해줘"
        ]

        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": example
                    })
                    st.rerun()


def show_recommended_places(places: list, session_token: str):
    if not places:
        return

    st.divider()
    st.write("**추천 맛집**")

    for place in places:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{place['name']}**")
                st.caption(f"{place['category']} | {place.get('address', '주소 없음')}")

                if place.get("reason"):
                    st.info(f"💡 {place['reason']}")

            with col2:
                if place.get("avg_rating"):
                    st.write(f"⭐ {place['avg_rating']}")

                # 피드백 버튼
                col_like, col_dislike = st.columns(2)
                with col_like:
                    if st.button("👍", key=f"like_{place['id']}_{session_token[:8]}"):
                        submit_feedback(session_token, place["id"], 1)
                with col_dislike:
                    if st.button("👎", key=f"dislike_{place['id']}_{session_token[:8]}"):
                        submit_feedback(session_token, place["id"], -1)


def submit_feedback(session_token: str, place_id: int, is_helpful: int):
    try:
        api_client.submit_feedback(session_token, place_id, is_helpful)
        st.toast("피드백이 전송되었습니다!" if is_helpful > 0 else "피드백이 전송되었습니다.")
    except Exception as e:
        st.error(f"피드백 전송 실패: {e}")
