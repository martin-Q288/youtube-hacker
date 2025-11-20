import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build
from PIL import Image
import os
import time
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="쇼핑 쇼츠 해커 (Global Master)", page_icon="🌍", layout="wide")

# ---------------------------------------------------------
# 2. API 키 입력 (Gemini + YouTube)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 1. Gemini 키 (분석용 - 필수)
    api_key = st.text_input("1. Google Gemini API Key", type="password")
    
    # 2. YouTube 키 (소싱용 - 선택)
    youtube_api_key = st.text_input("2. YouTube Data API Key", type="password", help="경쟁사 분석 및 소싱을 위해 필요합니다.")
    
    if not api_key:
        st.info("Gemini 키는 필수입니다.")
        st.warning("👉 [Gemini 키 발급](https://aistudio.google.com/app/apikey)")
        st.stop()
    else:
        st.success("Gemini 엔진 준비 완료!")
        st.write("Engine: **Gemini 2.5 Pro (Stable)**")
        
    if youtube_api_key:
        st.success("YouTube 레이더 가동!")

# 구글 AI 설정
try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"API 키 설정 오류: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 메인 화면
# ---------------------------------------------------------
st.title("🌍 유튜브 쇼핑 쇼츠 해커 (Master)")
st.markdown("### **7단계 심층 진단** + **경쟁사/유사상품 확장 소싱**을 한 번에!")
st.info("💡 **Rate Limit 자동 해결:** 분석 중 멈추지 않고 자동으로 대기했다가 재개합니다.")
st.markdown("---")

uploaded_files = st.file_uploader(
    "분석할 캡처 이미지를 모두 드래그하세요 (대량 가능)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

# ---------------------------------------------------------
# [함수 1] Rate Limit(429) 재시도 로직
# ---------------------------------------------------------
def generate_with_retry(model, inputs, retries=5):
    for attempt in range(retries):
        try:
            return model.generate_content(inputs)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                wait_time = 20 * (attempt + 1)
                st.toast(f"🚦 구글 사용량 제한! {wait_time}초 식히고 다시 갑니다... ({attempt+1}/{retries})", icon="⏳")
                time.sleep(wait_time)
                continue
            else:
                raise e
    return None

# ---------------------------------------------------------
# [함수 2] 유튜브 트렌드 레이더 (확장 검색)
# ---------------------------------------------------------
def search_viral_videos(api_key, keyword):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        # 최근 10일 이내 영상만
        ten_days_ago = (datetime.utcnow() - timedelta(days=10)).isoformat("T") + "Z"
        
        # 검색 실행
        search_response = youtube.search().list(
            q=keyword, part='id,snippet', maxResults=10, 
            publishedAfter=ten_days_ago, type='video', order='viewCount'
        ).execute()

        video_stats = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            
            # 상세 정보 (조회수)
            video_res = youtube.videos().list(part='statistics', id=video_id).execute()
            if not video_res['items']: continue
            view_count = int(video_res['items'][0]['statistics']['viewCount'])
            
            # 채널 정보 (구독자)
            channel_id = item['snippet']['channelId']
            channel_res = youtube.channels().list(part='statistics', id=channel_id).execute()
            try:
                sub_count = int(channel_res['items'][0]['statistics']['subscriberCount'])
            except:
                sub_count = 0
                
            # 알고리즘 선택 받은 영상 필터링 (구독자 100만 이하, 조회수가 구독자보다 높은 경우)
            if sub_count > 0 and sub_count < 1000000: 
                ratio = view_count / sub_count
                if ratio > 1.2: # 조회수가 구독자의 1.2배 이상인 '떡상' 영상만
                    video_stats.append({
                        'title': item['snippet']['title'],
                        'views': view_count,
                        'subs': sub_count,
                        'ratio': ratio,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'thumb': item['snippet']['thumbnails']['high']['url'],
                        'channel': item['snippet']['channelTitle']
                    })
        
        # 떡상 지수 순 정렬
        video_stats.sort(key=lambda x: x['ratio'], reverse=True)
        return video_stats[:3] # 키워드별 상위 3개만 리턴

    except Exception as e:
        st.error(f"유튜브 검색 오류: {e}")
        return []

# ---------------------------------------------------------
# 실행 로직
# ---------------------------------------------------------
if uploaded_files:
    st.success(f"📸 총 {len(uploaded_files)}장의 데이터가 준비되었습니다.")
    
    if st.button("🚀 심층 진단 및 글로벌 소싱 시작", type="primary"):
        
        all_analysis_results = []
        extracted_keywords = set() # 중복 제거된 키워드 저장소
        
        progress_text = "데이터 추출 및 확장 키워드 분석 중..."
        my_bar = st.progress(0, text=progress_text)
        
        # 모델 설정 (가장 안정적인 2.5 Pro)
        model = genai.GenerativeModel('gemini-2.5-pro')

        # [1단계] 개별 분석 & 키워드 확장 추출
        for i, uploaded_file in enumerate(uploaded_files):
            with st.expander(f"📄 {i+1}번 데이터 ({uploaded_file.name})", expanded=False):
                col_img, col_report = st.columns([1, 1.5])
                image = Image.open(uploaded_file)
                with col_img:
                    st.image(image, caption=f"데이터 {i+1}", use_container_width=True)
                
                with col_report:
                    try:
                        # 1. 데이터 추출 프롬프트
                        # 🔥 [수정 완료] 사장님이 원하시던 '5단계 눈높이 독설' 프롬프트
                        prompt = """
                        이 유튜브 분석표를 보고, '매출에 미친 마케팅 이사'가 초등학교 5학년 조카에게 설명하듯이 
                        아주 쉽고, 직관적이고, 뼈 때리게 분석해주세요.

                        **다음 5가지 항목을 반드시 포함하세요:**

                        1. **🚦 손님들이 알고 왔어? (유입의 품격)**: 
                           - "간판(썸네일) 보고 들어온 찐 손님(탐색)"인지, "그냥 지나가다 걸린 뜨내기 손님(피드)"인지 숫자로 따지세요.
                           - 탐색이 적으면 **"간판이 구려서 아무도 안 들어와!"** 라고 혼내주세요.
                        
                        2. **📉 3초 만에 도망갔어? (매력 측정)**: 
                           - 그래프가 시작하자마자 곤두박질치면 **"가게 문 열자마자 냄새나서 나갔어(3초 탈락)"** 라고 하고,
                           - 평평하게 유지되면 **"재밌어서 엉덩이 딱 붙이고 봤네(합격)"** 라고 칭찬하세요.
                        
                        3. **🗣️ 친구한테 소문 냈어? (바이럴)**: 
                           - (공유/좋아요 데이터가 보이면) "와 대박!" 하고 소문을 냈는지, "물건은 샀는데 쪽팔려서 숨겼는지" 확인하세요.

                        4. **🎯 엉뚱한 사람한테 팔았어? (타겟)**: 
                           - (성별/나이 데이터가 있다면) "어른들 술안주인데 초딩들이 보고 있네? 장사 헛했어!" 처럼 타겟이 맞는지 확인하세요.
                        
                        5. **💰 그래서 얼마 남겼어? (성적표)**: 
                           - 조회수 대비 돈을 얼마나 벌었는지 계산해서, **"이건 효자야(용돈 복사기)"** 인지 **"전기세만 날렸어(등짝 스매싱)"** 인지 등급(S~F)을 매기세요.
                        """
                        response = generate_with_retry(model, [prompt, image])
                        
                        if response:
                            st.markdown(response.text)
                            all_analysis_results.append(f"[{uploaded_file.name}]: {response.text}")
                            
                            # 2. 키워드 확장 프롬프트 (여기가 핵심!)
                            kw_prompt = """
                            이 이미지 속 영상의 '핵심 상품'을 파악하고, 유튜브에서 시장 조사를 하기 위한 **검색 키워드 3개**를 쉼표(,)로 구분해서 뽑아주세요.
                            
                            1. **정확한 상품명** (예: 연양갱)
                            2. **상위 카테고리/유사품** (예: 할매니얼 간식, 전통 디저트)
                            3. **영어 키워드** (글로벌 트렌드용, 예: Korean Jelly)
                            
                            출력 예시: 연양갱, 할매니얼 간식, Korean Jelly
                            """
                            kw_res = generate_with_retry(model, [kw_prompt, image])
                            
                            if kw_res:
                                # 키워드 분리해서 저장
                                kws = [k.strip() for k in kw_res.text.split(',')]
                                for k in kws:
                                    extracted_keywords.add(k)
                                st.caption(f"🔍 확장 검색어 발견: {', '.join(kws)}")
                                
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            my_bar.progress((i + 1) / len(uploaded_files))

        # [2단계] 글로벌 소싱 레이더 (YouTube API)
        if youtube_api_key and extracted_keywords:
            st.markdown("---")
            st.header("📡 경쟁사 및 유사상품 트렌드 (Expanded Radar)")
            st.info(f"AI가 추출한 **{len(extracted_keywords)}개 키워드**로 전 세계 유튜브를 스캔하여 **'구독자 대비 조회수'**가 높은 영상을 찾아냈습니다.")
            
            # 키워드별 검색 실행
            for kw in list(extracted_keywords)[:10]: # 너무 많으면 오래 걸리니 최대 10개 키워드만
                clean_kw = kw.replace("\n", "").strip()
                if len(clean_kw) < 2: continue
                
                viral_videos = search_viral_videos(youtube_api_key, clean_kw)
                
                if viral_videos:
                    st.subheader(f"🔍 키워드: '{clean_kw}'")
                    cols = st.columns(3) # 3개씩 보여주기
                    for idx, video in enumerate(viral_videos):
                        with cols[idx]:
                            st.image(video['thumb'], use_container_width=True)
                            st.markdown(f"**[{video['title']}]({video['url']})**")
                            st.caption(f"📺 채널: {video['channel']}")
                            st.caption(f"🔥 {video['views']:,}회 / 👤 {video['subs']:,}명")
                            st.caption(f"🚀 **떡상지수: {video['ratio']:.1f}배**")
                    st.markdown("---")
                else:
                    # 결과 없으면 조용히 패스
                    pass

        # [3단계] 7단계 심층 종합 리포트
        st.markdown("---")
        st.header("📝 AI 7단계 마스터 컨설팅 리포트")
        
        with st.spinner("AI가 최종 결론을 내리는 중입니다..."):
            try:
                combined_data = "\n".join(all_analysis_results)
                
                final_prompt = f"""
                당신은 연매출 100억 쇼핑몰을 만든 전설적인 유튜브 컨설턴트입니다.
                아래 데이터는 이 채널 영상들의 분석 결과입니다.
                
                이 데이터를 바탕으로 **7단계 심층 보고서**를 작성하세요.

                **[분석 데이터]**
                {combined_data}

                **[작성 가이드]**
                반드시 아래 Markdown 형식을 사용하여 작성하세요.

                ---
                ### 1. 🚦 신호등 진단 (Current Status)
                - 채널 상태 한 줄 정의 ("빛 좋은 개살구" 등)
                - 피드 의존도 vs 탐색 경쟁력 분석

                ### 2. 💰 손실 비용 계산기 (The Lost Money)
                - "사장님, 이 영상들 때문에 최소 **OOO만원**은 손해 보셨습니다."

                ### 3. 📉 이탈의 범인 찾기 (Killer Analysis)
                - 초반 3초 / 상품 설명 구간 등 공통적 이탈 패턴 지적

                ### 4. 🆚 가상 A/B 테스트 (What If)
                - 망한 영상 하나 골라서 "제목을 이렇게 바꿨다면 조회수 3배였을 겁니다" 예시 제시

                ### 5. 🏆 베스트 프랙티스 (The Winner)
                - 가장 잘한 점 칭찬 및 시리즈화 제안

                ### 6. 🔮 차기 대박 아이템 예언 (Next Cash Cow)
                - 시청자 성향 분석 후 "다음엔 무조건 이거 파세요" 구체적 상품 추천

                ### 7. 🚀 내일 당장 해야 할 숙제 3가지 (Action Plan)
                1. (구체적 지시)
                2. (구체적 지시)
                3. (구체적 지시)
                ---
                말투는 "사장님, 정신 차리세요" 느낌의 단호하고 확신에 찬 어조로 작성하세요.
                """
                
                # 종합 분석도 재시도 로직 적용 (텍스트만 보냄)
                final_response = generate_with_retry(model, [final_prompt])
                
                if final_response:
                    st.markdown(final_response.text)
                
            except Exception as e:
                st.error(f"종합 분석 중 오류 발생: {e}")

        st.balloons()