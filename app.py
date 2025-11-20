import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import time  # 대기 시간을 위해 추가

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼핑 쇼츠 해커 (종합진단)", page_icon="📊", layout="wide")

# ---------------------------------------------------------
# 2. API 키 입력 (개개인이 입력 가능하도록 변경)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    # 사장님 요청대로 개인이 직접 키를 넣는 방식으로 복구했습니다.
    api_key = st.text_input("Google Gemini API Key를 입력하세요", type="password")
    
    if not api_key:
        st.info("키를 입력해야 작동합니다.")
        st.warning("👉 무료 키 발급: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    else:
        st.success("API 키가 적용되었습니다!")
        st.write("Engine: **Gemini 2.5 Pro**")

# 구글 AI 설정
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"API 키 설정 오류: {e}")
        st.stop()
else:
    st.stop() # 키 없으면 여기서 멈춤

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("📊 유튜브 쇼핑 쇼츠 종합 진단기")
st.markdown("### 분석표를 몽땅 던져주세요. **개별 분석 후 '최종 결론'**을 내려드립니다.")
st.info("💡 **Rate Limit 자동 해결:** 분석 중 구글 제한에 걸리면 자동으로 대기했다가 재개합니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 모두 드래그하세요 (20장 이상 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

# ---------------------------------------------------------
# [함수] Rate Limit(429 에러) 방지용 재시도 함수
# ---------------------------------------------------------
def generate_with_retry(model, prompt, content, retries=3):
    for attempt in range(retries):
        try:
            return model.generate_content([prompt, content])
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                # 제한에 걸리면 30초 대기 후 재시도 (Pro 모델 무료 제한 대응)
                wait_time = 32 
                st.toast(f"🚦 구글 무료 사용량 제한! {wait_time}초 식히고 다시 갑니다...", icon="⏳")
                time.sleep(wait_time)
                continue
            else:
                raise e # 다른 에러면 그냥 띄움
    return None

if uploaded_files:
    st.success(f"📸 총 {len(uploaded_files)}장의 데이터가 준비되었습니다.")
    
    if st.button("🚀 종합 진단 시작하기", type="primary"):
        
        # 결과를 모아둘 리스트
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
                        # 사장님이 원하시는 모델명 유지
                        model = genai.GenerativeModel('gemini-2.5 pro') 
                        
                        individual_prompt = """
                        이 유튜브 스튜디오 분석표를 보고 핵심만 짧게 요약하세요.
                        1. 트래픽 소스 (탐색/피드 비율)
                        2. 시청 지속률 (이탈 여부)
                        3. 쇼핑 성과 (좋음/나쁨)
                        """
                        
                        # 🔥 [핵심 수정] 그냥 호출하지 않고, 재시도 함수를 통해 호출
                        response = generate_with_retry(model, individual_prompt, image)
                        
                        if response:
                            st.markdown(response.text)
                            all_analysis_results.append(f"[{uploaded_file.name} 분석결과]: {response.text}")
                        else:
                            st.error("분석 실패 (재시도 횟수 초과)")
                        
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            my_bar.progress((i + 1) / len(uploaded_files))
        
        # [2단계] 종합 결론 도출
        st.markdown("---")
        st.header("📝 AI 종합 컨설팅 보고서")
        
        with st.spinner("모든 데이터를 취합하여 최종 결론을 내리는 중입니다..."):
            try:
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
                
                # 종합 분석 때도 Rate Limit 걸릴 수 있으니 재시도 로직 적용 (이미지 없이 텍스트만)
                final_model = genai.GenerativeModel('gemini-2.5 pro')
                
                # 텍스트 전용 재시도 로직 (이미지가 없으므로 content 구조가 다름)
                final_response = None
                for attempt in range(3):
                    try:
                        final_response = final_model.generate_content(final_prompt)
                        break
                    except Exception as e:
                        if "429" in str(e) or "quota" in str(e).lower():
                            time.sleep(32)
                            continue
                        else:
                            raise e
                
                if final_response:
                    st.info("💡 모든 이미지 분석이 끝났습니다. 아래는 AI의 최종 결론입니다.")
                    st.markdown(final_response.text)
                
            except Exception as e:
                st.error(f"종합 분석 중 오류 발생: {e}")

        st.balloons()