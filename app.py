import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼핑 쇼츠 해커 (종합진단)", page_icon="📊", layout="wide")

# ---------------------------------------------------------
# 2. API 키 자동 감지 (Secrets)
# ---------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    with st.sidebar:
        st.success("🔑 자동 로그인 완료")
        st.write("Engine: **Gemini 2.5 Pro** (Stable)")
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
st.title("📊 유튜브 쇼핑 쇼츠 종합 진단기")
st.markdown("### 분석표를 몽땅 던져주세요. **개별 분석 후 '최종 결론'**을 내려드립니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 모두 드래그하세요 (20장 이상 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"📸 총 {len(uploaded_files)}장의 데이터가 준비되었습니다.")
    
    if st.button("🚀 종합 진단 시작하기", type="primary"):
        
        # 결과를 모아둘 리스트 (메모장 역할)
        all_analysis_results = []
        
        progress_text = "개별 데이터를 뜯어보는 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        # [1단계] 개별 이미지 순차 분석
        for i, uploaded_file in enumerate(uploaded_files):
            
            with st.expander(f"📄 {i+1}번 개별 분석 ({uploaded_file.name})", expanded=False):
                col_img, col_report = st.columns([1, 1.5])
                
                image = Image.open(uploaded_file)
                with col_img:
                    st.image(image, caption=f"데이터 {i+1}", use_container_width=True)
                
                with col_report:
                    try:
                        model = genai.GenerativeModel('gemini-2.5-pro')
                        
                        # 개별 분석 프롬프트
                        individual_prompt = """
                        이 유튜브 스튜디오 분석표를 보고 핵심만 짧게 요약하세요.
                        1. 트래픽 소스 (탐색/피드 비율)
                        2. 시청 지속률 (이탈 여부)
                        3. 쇼핑 성과 (좋음/나쁨)
                        """
                        
                        response = model.generate_content([individual_prompt, image])
                        st.markdown(response.text)
                        
                        # 결과 저장 (나중에 종합하기 위해)
                        all_analysis_results.append(f"[{uploaded_file.name} 분석결과]: {response.text}")
                        
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            my_bar.progress((i + 1) / len(uploaded_files))
        
        # [2단계] 종합 결론 도출 (여기가 핵심!)
        st.markdown("---")
        st.header("📝 AI 종합 컨설팅 보고서")
        
        with st.spinner("모든 데이터를 취합하여 최종 결론을 내리는 중입니다..."):
            try:
                # 저장된 모든 분석 결과를 합쳐서 AI에게 전달
                combined_data = "\n".join(all_analysis_results)
                
                final_prompt = f"""
                당신은 유튜브 쇼핑 채널을 컨설팅하는 수석 분석가입니다.
                아래 내용은 이 채널의 영상 {len(uploaded_files)}개에 대한 개별 분석 결과입니다.
                
                이 데이터를 **통틀어서 봤을 때** 발견되는 패턴과 문제점을 찾아내고,
                사장님에게 아주 꼼꼼하고 직설적인 피드백을 작성하세요.

                **[분석 데이터 모음]**
                {combined_data}

                **[작성 가이드]**
                1. **현재 상태 진단 (Fact Check)**:
                   - 전체적으로 '피드 노출' 위주인가, '탐색 유입' 위주인가?
                   - 쇼핑 전환이 잘 되는 영상들의 공통점은 무엇인가?
                   - 망한 영상들의 공통적인 패착은 무엇인가?

                2. **잘하고 있는 점 (칭찬)**:
                   - 데이터에서 발견된 긍정적인 신호를 구체적으로 언급하세요.

                3. **반드시 고쳐야 할 점 (쓴소리)**:
                   - 썸네일/제목 패턴의 문제점
                   - 초반 3초 후킹의 문제점
                   - 상품 선정의 문제점 등을 적나라하게 지적하세요.

                4. **향후 행동 강령 (Action Plan)**:
                   - "당장 내일부터 OOO을 하세요" 형태의 구체적인 지침 3가지를 주세요.

                말투는 정중하지만, 데이터에 기반하여 냉철하고 확신에 찬 어조로 작성하세요.
                """
                
                final_model = genai.GenerativeModel('gemini-2.5-pro')
                final_response = final_model.generate_content(final_prompt)
                
                st.info("💡 모든 이미지 분석이 끝났습니다. 아래는 AI의 최종 결론입니다.")
                st.markdown(final_response.text)
                
            except Exception as e:
                st.error(f"종합 분석 중 오류 발생: {e}")

        st.balloons()