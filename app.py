import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import time

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼핑 쇼츠 해커 (Standard)", page_icon="📊", layout="wide")

# ---------------------------------------------------------
# 2. API 키 입력 (개별 입력 방식)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Google Gemini API Key를 입력하세요", type="password")
    
    if not api_key:
        st.info("키를 입력해야 작동합니다.")
        st.warning("👉 무료 키 발급: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    else:
        st.success("API 키가 적용되었습니다!")
        st.write("Engine: **Gemini 2.5 Pro (Stable)**")

# 구글 AI 설정 (표준 방식)
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API 키 설정 오류: {e}")
        st.stop()
else:
    st.stop()

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("📊 유튜브 쇼핑 쇼츠 종합 진단기")
st.markdown("### 분석표를 몽땅 던져주세요. **에러 없는 표준 엔진**이 분석합니다.")
st.info("💡 **자동 대기 시스템:** 구글 사용량 제한(429)에 걸리면 알아서 기다렸다가 다시 합니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 모두 드래그하세요 (대량 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

# ---------------------------------------------------------
# [함수] 재시도 로직 (Rate Limit 해결사)
# ---------------------------------------------------------
def generate_with_retry(model, inputs, retries=3):
    for attempt in range(retries):
        try:
            # 표준 방식 호출
            return model.generate_content(inputs)
        except Exception as e:
            # 429 에러(Rate Limit)가 뜨면 대기
            if "429" in str(e) or "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                wait_time = 20  # 20초 대기
                st.toast(f"🚦 사용량 제한 감지! {wait_time}초 쉬었다 갑니다... ({attempt+1}/{retries})", icon="⏳")
                time.sleep(wait_time)
                continue
            else:
                raise e # 다른 에러는 그냥 표시
    return None

if uploaded_files:
    st.success(f"📸 총 {len(uploaded_files)}장의 데이터가 준비되었습니다.")
    
    if st.button("🚀 종합 진단 시작하기", type="primary"):
        
        all_analysis_results = []
        
        progress_text = "데이터를 안전하게 분석 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        # 모델 설정 (가장 안정적인 2.5 Pro 사용)
        model = genai.GenerativeModel('gemini-2.5-pro')

        # [1단계] 개별 이미지 순차 분석
        for i, uploaded_file in enumerate(uploaded_files):
            
            with st.expander(f"📄 {i+1}번 개별 분석 ({uploaded_file.name})", expanded=False):
                col_img, col_report = st.columns([1, 1.5])
                
                image = Image.open(uploaded_file)
                with col_img:
                    st.image(image, caption=f"데이터 {i+1}", use_container_width=True)
                
                with col_report:
                    try:
                        individual_prompt = """
                        이 유튜브 스튜디오 분석표를 보고 핵심만 짧게 요약하세요.
                        1. 트래픽 소스 (탐색/피드 비율)
                        2. 시청 지속률 (이탈 여부)
                        3. 쇼핑 성과 (좋음/나쁨)
                        """
                        
                        # 🔥 재시도 함수를 통해 안전하게 호출
                        response = generate_with_retry(model, [individual_prompt, image])
                        
                        if response:
                            st.markdown(response.text)
                            all_analysis_results.append(f"[{uploaded_file.name} 분석결과]: {response.text}")
                        else:
                            st.error("분석 실패 (재시도 횟수 초과)")
                        
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            # 진행률 업데이트
            my_bar.progress((i + 1) / len(uploaded_files))
        
        # [2단계] 종합 결론 도출
        st.markdown("---")
        st.header("📝 AI 종합 컨설팅 보고서")
        
        with st.spinner("최종 결론을 내리는 중입니다..."):
            try:
                combined_data = "\n".join(all_analysis_results)
                
                final_prompt = f"""
                당신은 유튜브 쇼핑 채널 컨설턴트입니다.
                아래는 이 채널 영상 {len(uploaded_files)}개의 분석 결과입니다.
                
                이 데이터를 종합하여 사장님에게 꼼꼼한 피드백을 작성하세요.

                **[분석 데이터 모음]**
                {combined_data}

                **[작성 가이드]**
                1. **현재 상태 진단**: '피드 노출' 위주인가, '탐색 유입' 위주인가?
                2. **잘하고 있는 점**: 긍정적인 신호.
                3. **반드시 고쳐야 할 점**: 썸네일, 초반 후킹, 상품 선정의 문제점.
                4. **향후 행동 강령**: 당장 내일부터 해야 할 구체적 지침 3가지.

                말투는 정중하지만 냉철하게 작성하세요.
                """
                
                # 종합 분석도 재시도 로직 적용
                final_response = generate_with_retry(model, final_prompt)
                
                if final_response:
                    st.info("💡 모든 이미지 분석이 끝났습니다. 아래는 AI의 최종 결론입니다.")
                    st.markdown(final_response.text)
                
            except Exception as e:
                st.error(f"종합 분석 중 오류 발생: {e}")

        st.balloons()