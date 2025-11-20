import streamlit as st
from google import genai
from PIL import Image
import os

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼츠 분석기 (Gemini 3.0 Pro)", page_icon="🚀", layout="wide")

# ---------------------------------------------------------
# 2. API 키 자동 감지 & 신형 Client 연결
# ---------------------------------------------------------
api_key = None

# Secrets에서 키 확인
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    with st.sidebar:
        st.success("🔑 사장님 자동 로그인 (New SDK)")
        st.write("Engine: **Gemini 3.0 Pro Preview**")
else:
    with st.sidebar:
        st.header("⚙️ 설정")
        api_key = st.text_input("Google Gemini API Key", type="password")

if not api_key:
    st.warning("👈 API 키가 필요합니다.")
    st.stop()

# 🔥 [핵심 변경] 사장님이 알려주신 신형 클라이언트 방식 적용
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"클라이언트 연결 오류: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("📊 유튜브 쇼핑 쇼츠 정밀 진단기 (v3.0)")
st.markdown("### **Gemini 3.0 Pro** (New SDK) 가 분석합니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 모두 드래그하세요 (대량 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"📸 {len(uploaded_files)}장의 데이터가 준비되었습니다.")
    
    if st.button("🚀 Gemini 3.0 Pro로 진단 시작", type="primary"):
        
        # 결과 저장용 리스트 (종합 진단을 위해)
        all_analysis_results = []
        
        progress_text = "Gemini 3.0이 데이터를 뜯어보는 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        # -----------------------------------------------------
        # [1단계] 개별 이미지 순차 분석
        # -----------------------------------------------------
        for i, uploaded_file in enumerate(uploaded_files):
            
            with st.expander(f"📄 {i+1}번 개별 분석 ({uploaded_file.name})", expanded=False):
                col_img, col_report = st.columns([1, 1.5])
                
                image = Image.open(uploaded_file)
                with col_img:
                    st.image(image, caption=f"데이터 {i+1}", use_container_width=True)
                
                with col_report:
                    try:
                        # 프롬프트 작성
                        vision_prompt = """
                        이 유튜브 스튜디오 분석표를 보고 다음 3가지만 핵심적으로 요약하세요.
                        절대 길게 쓰지 말고 데이터 위주로 팩트만 말하세요.
                        
                        1. 트래픽 소스 (탐색 vs 피드 비율)
                        2. 시청 지속률 (이탈 구간 및 그래프 모양)
                        3. 쇼핑 성과 (조회수 대비 수익 효율)
                        """
                        
                        # 🔥 [핵심 변경] 사장님이 원하신 신형 호출 방식
                        response = client.models.generate_content(
                            model="gemini-3-pro-preview",
                            contents=[vision_prompt, image]
                        )
                        
                        st.markdown(response.text)
                        
                        # 결과 저장
                        all_analysis_results.append(f"[{uploaded_file.name} 분석결과]: {response.text}")
                        
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            my_bar.progress((i + 1) / len(uploaded_files))
        
        # -----------------------------------------------------
        # [2단계] 종합 결론 도출
        # -----------------------------------------------------
        st.markdown("---")
        st.header("📝 AI 종합 컨설팅 보고서")
        
        with st.spinner("Gemini 3.0 Pro가 최종 결론을 내리는 중입니다..."):
            try:
                combined_data = "\n".join(all_analysis_results)
                
                final_prompt = f"""
                당신은 대한민국 최고의 유튜브 쇼핑 채널 컨설턴트입니다.
                아래 내용은 이 채널의 영상 {len(uploaded_files)}개에 대한 개별 분석 데이터입니다.
                
                이 데이터를 **통틀어서 봤을 때** 발견되는 패턴과 문제점을 찾아내고,
                채널 주인에게 아주 꼼꼼하고 직설적인 피드백을 작성하세요.

                **[분석 데이터 모음]**
                {combined_data}

                **[작성 가이드]**
                1. **🩺 현재 상태 정밀 진단 (Fact Check)**:
                   - 전체적으로 '피드 노출' 위주인가, '탐색 유입' 위주인가?
                   - 성공한 영상들의 공통 공식은?
                   - 실패한 영상들의 공통 패착은?

                2. **🚀 당장 해야 할 행동 강령 (Action Plan)**:
                   - 구체적이고 실행 가능한 지침 3가지를 내리세요.

                말투는 전문가답게, 확신에 차고 냉철하게 작성하세요.
                """
                
                # 🔥 [핵심 변경] 텍스트 생성도 신형 방식으로 호출
                final_response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    contents=final_prompt
                )
                
                st.markdown(final_response.text)
                
            except Exception as e:
                st.error(f"종합 분석 중 오류 발생: {e}")

        st.balloons()