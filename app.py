import os

from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# .env에서 환경변수 읽기
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일 또는 Streamlit Secrets를 확인해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# 세션 상태 초기화: 마지막 입력 상황 저장용
if "user_context" not in st.session_state:
    st.session_state["user_context"] = None

st.title("상황 맞춤 식사 메뉴 추천기")

st.write("아래 상황을 입력하면, ChatGPT가 오늘 먹기 좋은 메뉴를 추천해 줍니다.")

# 입력 폼
with st.form("meal_form"):
    num_people = st.number_input("인원 수", min_value=1, max_value=20, value=2)

    relationship = st.selectbox(
        "함께 먹는 사람과의 관계",
        ["친구", "동료", "가족", "연인", "혼자", "기타"],
    )

    # 새로 추가: 시간대 선택
    time_of_day = st.selectbox(
        "식사 시간대",
        ["아침", "점심", "저녁", "야식", "기타"],
        index=1,  # 기본값: 점심
    )

    last_meal = st.text_input("최근 먹은 음식")

    meal_type = st.radio(
        "식사 형태",
        ["배달", "외식", "집에서 요리", "기타"],
        index=1, # 기본값: 외식
    )

    budget = st.selectbox(
        "1인당 예산",
        ["상관없음", "1만 원 이하", "1~2만 원", "2만 원 이상"],
        index=2,  # 기본값: "1~2만 원"
    )

    spicy = st.selectbox(
        "매운맛 선호도",
        ["매운 것 잘 못 먹음", "보통", "매운 거 좋아함"],
        index=1,  # 기본값: "보통"
    )

    restrictions = st.text_input("알레르기 / 금지 음식 (없으면 비워두기)")
    notes = st.text_area(
        "기타 요청사항 (최대한 구체적으로 적어주세요)",
        placeholder="예: 가볍게, 술안주 위주, 건강식, 빨리 먹을 수 있게, 느끼한 건 싫어요, 토마토가 들어간 요리 등",
    )

    submitted = st.form_submit_button("메뉴 추천 받기")

# 폼 입력값으로 상황 문자열 구성 (제출 여부와 상관없이 항상 만들 수 있음)
user_context = f"""
인원 수: {num_people}
관계: {relationship}
식사 시간대: {time_of_day}
최근 먹은 음식: {last_meal}
식사 형태: {meal_type}
1인당 예산: {budget}
매운맛 선호: {spicy}
알레르기/금지 음식: {restrictions}
기타 요청사항: {notes}
"""

# 폼이 제출되면 현재 상황을 세션에 저장
if submitted:
    st.session_state["user_context"] = user_context

st.write("---")

# 이전에 한 번이라도 추천을 받은 경우에만 다시 추천 버튼 활성화
regenerate = st.button(
    "메뉴가 마음에 안 들어요, 다시 추천해줘",
    disabled=st.session_state["user_context"] is None,
)

# 실제로 API를 호출해야 하는지 여부 결정
should_call_api = submitted or regenerate

if should_call_api:
    # 다시 추천일 경우에는 세션에 저장된 상황을 사용
    context_for_prompt = st.session_state["user_context"] or user_context

    prompt = f"""
너는 한국 사용자를 위한 식사 메뉴 추천 도우미야.
아래 상황을 보고 오늘 먹기 좋은 메뉴를 3가지 추천해 줘.

각 메뉴에 대해:
- 메뉴 이름 (한글로)
- 간단한 설명
- 왜 이 상황과 시간대에 잘 맞는지

단, 사용자가 다시 추천을 요청한 경우에는
가능하면 이전 추천과 최대한 겹치지 않는 다른 메뉴들을 위주로 추천해줘.

상황:
{context_for_prompt}
"""

    with st.spinner("메뉴를 고민하는 중입니다..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=1.0,  # 다시 추천 시 메뉴가 더 다양하게 나오도록 온도 설정
            messages=[
                {
                    "role": "system",
                    "content": "너는 현실적이고 세심한 한국인 식사 메뉴 추천 도우미야.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content

    st.subheader("추천 결과")
    st.markdown(answer)
