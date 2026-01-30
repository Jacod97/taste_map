import streamlit as st
from client.api import api_client

CATEGORIES = [
    ("korean", "한식"),
    ("japanese", "일식"),
    ("chinese", "중식"),
    ("western", "양식"),
    ("cafe", "카페"),
    ("bar", "술집"),
    ("fastfood", "패스트푸드"),
    ("dessert", "디저트"),
    ("other", "기타"),
]

CATEGORY_MAP = {code: name for code, name in CATEGORIES}
CATEGORY_REVERSE_MAP = {name: code for code, name in CATEGORIES}


def show_add_place():
    st.title("➕ 맛집 등록")

    with st.form("add_place_form"):
        name = st.text_input("맛집 이름 *")
        category_names = [name for _, name in CATEGORIES]
        category = st.selectbox("카테고리", category_names)

        st.write("**위치 정보**")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("위도 *", value=37.5665, format="%.6f")
        with col2:
            longitude = st.number_input("경도 *", value=126.9780, format="%.6f")

        address = st.text_input("주소")
        memo = st.text_area("메모")
        tags = st.text_input("태그 (쉼표로 구분)")
        visibility = st.selectbox("공개 설정", ["나만 보기", "공개"])

        submitted = st.form_submit_button("등록", use_container_width=True)

        if submitted:
            if not name:
                st.error("맛집 이름을 입력해주세요.")
                return

            try:
                data = {
                    "name": name,
                    "category": CATEGORY_REVERSE_MAP.get(category, "other"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "address": address or None,
                    "memo": memo or None,
                    "tags": tags or None,
                    "visibility": "private" if visibility == "나만 보기" else "public"
                }
                result = api_client.create_place(data)
                st.success(f"'{result['name']}' 맛집이 등록되었습니다!")
            except Exception as e:
                st.error(f"등록 실패: {e}")

    st.divider()
    st.caption("💡 위도/경도는 네이버 지도나 구글 지도에서 확인할 수 있습니다.")
