import streamlit as st
import folium
from streamlit_folium import st_folium
from client.api import api_client
from client.views.places import CATEGORY_MAP


def show_map_view():
    st.title("🗺️ 내 맛집 지도")

    # 상단 필터/검색
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        keyword = st.text_input("검색", placeholder="맛집 이름, 태그로 검색", label_visibility="collapsed")
    with col2:
        category_options = ["전체"] + [name for name in CATEGORY_MAP.values()]
        category_filter = st.selectbox("카테고리", category_options, label_visibility="collapsed")
    with col3:
        min_rating = st.selectbox("평점", [None, 4.0, 3.0, 2.0], format_func=lambda x: "전체" if x is None else f"⭐{x}+", label_visibility="collapsed")

    # 맛집 데이터 로드
    places = load_places(keyword, category_filter, min_rating)

    # 레이아웃: 지도 | 상세정보
    map_col, detail_col = st.columns([2, 1])

    with map_col:
        # 지도 생성
        m = create_map(places)
        map_data = st_folium(
            m,
            width=None,
            height=500,
            returned_objects=["last_object_clicked"]
        )

        # 마커 클릭 감지
        if map_data and map_data.get("last_object_clicked"):
            clicked = map_data["last_object_clicked"]
            clicked_lat = clicked.get("lat")
            clicked_lng = clicked.get("lng")

            # 클릭한 위치와 가장 가까운 맛집 찾기
            for place in places:
                if abs(place["latitude"] - clicked_lat) < 0.0001 and abs(place["longitude"] - clicked_lng) < 0.0001:
                    st.session_state.selected_place = place
                    break

    with detail_col:
        if st.session_state.selected_place:
            show_place_detail(st.session_state.selected_place)
        else:
            st.info("지도에서 맛집을 클릭하세요")

            # 맛집 목록
            st.divider()
            st.write(f"**등록된 맛집 ({len(places)}개)**")
            for place in places[:10]:
                with st.container(border=True):
                    if st.button(f"📍 {place['name']}", key=f"list_{place['id']}", use_container_width=True):
                        st.session_state.selected_place = place
                        st.session_state.map_center = [place["latitude"], place["longitude"]]
                        st.rerun()


def load_places(keyword: str, category: str, min_rating: float) -> list:
    try:
        # 카테고리 코드 변환
        category_code = None
        if category != "전체":
            for code, name in CATEGORY_MAP.items():
                if name == category:
                    category_code = code
                    break

        result = api_client.search_places(
            keyword=keyword if keyword else None,
            category=category_code,
            min_rating=min_rating,
            only_mine=True
        )
        return result.get("places", [])
    except Exception as e:
        st.error(f"맛집 로드 실패: {e}")
        return []


def create_map(places: list) -> folium.Map:
    # 맛집이 있으면 중심점 계산
    if places:
        avg_lat = sum(p["latitude"] for p in places) / len(places)
        avg_lng = sum(p["longitude"] for p in places) / len(places)
        center = [avg_lat, avg_lng]
    else:
        center = st.session_state.map_center

    m = folium.Map(
        location=center,
        zoom_start=st.session_state.map_zoom,
        tiles="cartodbpositron"
    )

    # 마커 추가
    for place in places:
        # 카테고리별 색상
        color = get_marker_color(place["category"])

        # 팝업 내용
        popup_html = f"""
        <b>{place['name']}</b><br>
        {CATEGORY_MAP.get(place['category'], place['category'])}<br>
        {'⭐ ' + str(place['avg_rating']) if place.get('avg_rating') else '평점 없음'}
        """

        folium.Marker(
            location=[place["latitude"], place["longitude"]],
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=place["name"],
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa")
        ).add_to(m)

    return m


def get_marker_color(category: str) -> str:
    colors = {
        "korean": "red",
        "japanese": "blue",
        "chinese": "orange",
        "western": "purple",
        "cafe": "pink",
        "bar": "darkred",
        "fastfood": "cadetblue",
        "dessert": "lightred",
        "other": "gray"
    }
    return colors.get(category, "gray")


def show_place_detail(place: dict):
    st.subheader(f"📍 {place['name']}")

    # 닫기 버튼
    if st.button("✕ 닫기", use_container_width=True):
        st.session_state.selected_place = None
        st.rerun()

    st.divider()

    # 기본 정보
    category_name = CATEGORY_MAP.get(place["category"], place["category"])
    st.write(f"**카테고리:** {category_name}")

    if place.get("address"):
        st.write(f"**주소:** {place['address']}")

    if place.get("avg_rating"):
        st.write(f"**평점:** ⭐ {place['avg_rating']} ({place.get('review_count', 0)}개 리뷰)")

    if place.get("tags"):
        st.write(f"**태그:** {place['tags']}")

    if place.get("memo"):
        st.write(f"**메모:** {place['memo']}")

    visibility = "🌐 공개" if place["visibility"] == "public" else "🔒 비공개"
    st.caption(visibility)

    # 리뷰 섹션
    st.divider()
    show_reviews_section(place["id"])

    # 수정/삭제
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ 수정", use_container_width=True):
            st.session_state.edit_place = place
            st.session_state.show_edit_modal = True
    with col2:
        if st.button("🗑️ 삭제", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_delete") == place["id"]:
                try:
                    api_client.delete_place(place["id"])
                    st.session_state.selected_place = None
                    st.session_state.confirm_delete = None
                    st.success("삭제되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 실패: {e}")
            else:
                st.session_state.confirm_delete = place["id"]
                st.warning("다시 클릭하면 삭제됩니다")


def show_reviews_section(place_id: int):
    st.write("**리뷰**")

    try:
        reviews = api_client.get_place_reviews(place_id)

        if reviews:
            for review in reviews[:5]:
                with st.container(border=True):
                    st.write(f"⭐ {review['rating']}")
                    if review.get("content"):
                        st.write(review["content"])
        else:
            st.caption("아직 리뷰가 없습니다")

        # 리뷰 작성
        with st.expander("리뷰 작성"):
            rating = st.slider("평점", 1.0, 5.0, 3.0, 0.5, key=f"rating_{place_id}")
            content = st.text_area("내용", key=f"content_{place_id}")

            if st.button("등록", key=f"submit_{place_id}"):
                try:
                    api_client.create_review(place_id, rating, content)
                    st.success("리뷰가 등록되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"등록 실패: {e}")

    except Exception as e:
        st.error(f"리뷰 로드 실패: {e}")
