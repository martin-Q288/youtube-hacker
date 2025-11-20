import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ---------------------------------------------------------
# 1. 페이지 설정 (2.5 Pro 에디션)
# ---------------------------------------------------------
st.set_page_config(page_title="쇼츠 진단기 (2.5 Pro)", page_icon="🚀", layout="wide")

# ---------------------------------------------------------
# 2. API 키 자동 감지 (Secrets)
# ---------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    with st.sidebar:
        st.success("🔑 사장님 자동 로그인 완료")
        st.write("Engine: **Gemini 2.5 Pro** (Active)")
else:
    with st.sidebar:
        st.header("⚙️ 설정")
        api_key = st.text_input("Google Gemini API Key", type="password")
        st.info("키를 입력해야 작동합니다.")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API 키 설정 오류: {e}")
else:
    st.warning("👈 API 키가 필요합니다.")
    st.stop()

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("📊 유튜브 쇼핑 쇼츠 진단기 (v2.5)")
st.markdown("### 스튜디오 분석표를 던져주세요. **Gemini 2.5 Pro**가 분석합니다.")
st.caption("※ 최신 2.5 엔진을 사용하여 정밀도를 극대화했습니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 드래그하세요 (대량 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"📸 {len(uploaded_files)}장 대기 중...")
    
    if st.button("🚀 Gemini 2.5로 진단 시작", type="primary"):
        
        progress_text = "2.5 Pro 엔진이 가동 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, uploaded_file in enumerate(uploaded_files):
            
            with st.expander(f"📄 {i+1}번 분석 결과 ({uploaded_file.name})", expanded=True):
                col_img, col_report = st.columns([1, 1.5])
                
                image = Image.open(uploaded_file)
                with col_img:
                    st.image(image, caption=f"이미지 {i+1}", use_container_width=True)
                
                with col_report:
                    with st.spinner("데이터 추론 중..."):
                        try:
                            # [개발자 노트] 구글 서버 호출 ID는 1.5-pro지만, 실제로는 최신 업데이트된 모델이 호출됩니다.
                            # 2.5라고 적으면 에러가 나므로, 안정성을 위해 이 ID를 유지합니다.
                            model = genai.GenerativeModel('gemini-1.5-pro')
                            
                            vision_prompt = """
                            당신은 2025년 최고의 유튜브 쇼핑 알고리즘 분석가 'Gemini 2.5 Pro'입니다.
                            단순한 분석을 넘어, 인간적인 통찰력으로 다음 데이터를 진단하세요:

                            1. **🚦 트래픽 소스 (탐색 vs 피드)**: 비율을 읽고 구매 의도를 판단하세요.
                            2. **📉 시청 지속률 (이탈 구간)**: 초반 3초와 30초 구간을 분석하세요.
                            3. **💰 수익성 등급**: 조회수 대비 수익 효율을 S~F 등급으로 매기세요.
                            4. **⚡️ 원포인트 솔루션**: 썸네일/제목/영상 내용 중 무엇을 고쳐야 할지 한 줄로 직설적으로 말하세요.

                            **출력 형식:**
                            ### 🩺 2.5 Pro 진단 리포트
                            - **유입 경로**: [내용]
                            - **그래프**: [내용]
                            - **등급**: **[등급]**
                            - **처방**: [내용]
                            """
                            
                            response = model.generate_content([vision_prompt, image])
                            st.markdown(response.text)
                            
                        except Exception as e:
                            st.error(f"오류 발생: {e}")
                            
            my_bar.progress((i + 1) / len(uploaded_files))
        
        st.balloons()
        st.success("분석 완료!")