import streamlit as st
import google.generativeai as genai
from PIL import Image

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼핑 쇼츠 해커 (구글 Pro버전)", page_icon="🍗", layout="wide")

# ---------------------------------------------------------
# 2. 사이드바: 구글 API 키 입력
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정 (2025 Pro 에디션)")
    api_key = st.text_input("Google Gemini API Key를 입력하세요", type="password")
    st.info("구글 AI Studio에서 받은 무료 키를 넣으세요.")
    st.markdown("---")
    st.write("Powered by Google Gemini Pro")

# 구글 AI 설정
if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("👈 왼쪽 사이드바에 Google API Key를 입력해주세요!")
    st.stop()

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("🍗 유튜브 쇼핑 쇼츠 해커 (Pro 엔진)")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 제목 심폐소생기", "📊 분석표 진단기"])

# ---------------------------------------------------------
# 기능 1: 제목 생성 (Pro 모델 적용)
# ---------------------------------------------------------
with tab1:
    st.header("죽어가는 제목을 '매출'로 바꿉니다")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        original_title = st.text_input("기존 제목을 입력하세요", placeholder="예: 80년을 버틴 과자")
        product_name = st.text_input("판매할 제품명은?", placeholder="예: 연양갱")
        
        if st.button("💰 돈 버는 제목 5개 생성하기", type="primary"):
            if not original_title or not product_name:
                st.error("제목과 제품명을 모두 입력해주세요!")
            else:
                with st.spinner("최신 Pro AI가 머리를 굴리는 중입니다..."):
                    try:
                        # 🔥 모델을 Pro 버전으로 교체했습니다!
                        model = genai.GenerativeModel('gemini-2.5-pro')
                        
                        prompt = f"""
                        당신은 2025년 한국 시장에 특화된 '식품 커머스 전문 카피라이터'입니다.
                        사용자가 입력한 제목: "{original_title}"
                        판매 제품: "{product_name}"
                        
                        이 제목을 쇼핑 전환율이 극대화되도록 다음 4가지 공식에 맞춰 수정하고, 추가로 1개는 자유롭게 제안하세요.
                        반드시 제목 앞이나 뒤에 [꾸덕, 바삭, 육즙, 10분컷, 종결] 같은 감각적 키워드를 상황에 맞게 넣으세요.

                        출력 형식:
                        1. 💸 맛집 털기형 (가성비 강조)
                        2. 💊 게으른 미식가형 (편의성 강조)
                        3. 👑 아는 맛의 공포형 (비밀/권위 강조)
                        4. 🔥 품절 대란 탑승형 (희소성 강조)
                        5. 🧪 AI 추천 (자유 형식)

                        설명 없이 제목만 5줄로 깔끔하게 출력하세요.
                        """
                        
                        response = model.generate_content(prompt)
                        st.success("생성 완료! (Pro 모델이라 더 확실합니다)")
                        st.code(response.text, language="text")
                        
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                        st.info("혹시 404 오류가 계속되면, 구글 키에 'Pro' 모델 권한이 있는지 확인해보세요!")

# ---------------------------------------------------------
# 기능 2: 이미지 분석 (Pro 모델 적용)
# ---------------------------------------------------------
with tab2:
    st.header("유튜브 스튜디오 캡처를 분석합니다")
    
    uploaded_file = st.file_uploader("캡처 이미지 업로드 (JPG, PNG)", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 이미지", width=400)
        
        if st.button("🔍 AI 정밀 분석 시작"):
            with st.spinner("Pro AI가 그래프를 정밀 분석 중입니다..."):
                try:
                    # 🔥 여기도 Pro 버전으로 교체!
                    model = genai.GenerativeModel('gemini-2.5-pro')
                    
                    vision_prompt = """
                    이 이미지는 유튜브 스튜디오 분석 화면입니다.
                    다음 항목을 분석해서 한국어로 리포트를 써주세요.
                    
                    1. **트래픽 소스 분석**: '쇼츠 피드' 비중과 '탐색 기능(또는 검색)' 비중이 대략 몇 %인지 숫자를 읽어서 알려주세요.
                    2. **시청 지속률 분석**: 그래프가 초반에 급격히 꺾이는지, 완만한지 설명하고 이것이 '피드형'인지 '탐색형'인지 판단하세요.
                    3. **쇼핑 적합도 평가**: 조회수 대비 수익 효율이 좋아 보이는지 나빠 보이는지 평가하세요.
                    4. **최종 조언**: 이 채널이 돈을 더 벌기 위해 썸네일을 고쳐야 할지, 영상을 고쳐야 할지 한 줄로 조언하세요.
                    
                    형식:
                    ## 📊 구글 Pro AI 분석 리포트
                    - **트래픽 성향**: [내용]
                    - **그래프 패턴**: [내용]
                    - **종합 등급**: [S/A/B/C 중 하나]
                    - **닥터의 처방**: [내용]
                    """
                    
                    response = model.generate_content([vision_prompt, image])
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")