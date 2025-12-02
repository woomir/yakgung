"""
DrugFood Guard - Streamlit Application
약궁 (YakGung) - 약물-음식 상호작용 확인 AI Agent
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import uuid
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher
import html

# 경로 설정
APP_DIR = Path(__file__).parent
sys.path.append(str(APP_DIR))

from config import RISK_LEVELS, LLM_PROVIDER, OPENAI_API_KEY, GOOGLE_API_KEY
from db.database import UserDrugDB
from rag.vector_store import DrugFoodRAG
from agent.agent import DrugFoodAgent

# ===== 페이지 설정 =====
st.set_page_config(
    page_title="약궁 (YakGung) 💊🥗",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS 스타일 =====
st.markdown("""
<style>
    /* 메인 헤더 (배너 스타일) */
    .main-header-container {
        background: linear-gradient(135deg, #1e3a5f 0%, #142841 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .main-header-subtitle {
        font-size: 1rem;
        opacity: 0.8;
    }
    
    /* 카드 스타일 */
    .drug-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* 위험도 스타일 */
    .risk-danger { 
        background: #ffebee; 
        border-left: 4px solid #dc3545; 
        padding: 1rem; 
        border-radius: 8px; 
        margin: 0.5rem 0;
    }
    .risk-warning { 
        background: #fff3e0; 
        border-left: 4px solid #fd7e14; 
        padding: 1rem; 
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .risk-caution { 
        background: #fffde7; 
        border-left: 4px solid #ffc107; 
        padding: 1rem; 
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .risk-safe { 
        background: #e8f5e9; 
        border-left: 4px solid #28a745; 
        padding: 1rem; 
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
    }
    
    /* 카테고리 버튼 색상 (커스텀) */
    div[data-testid="column"] > div > div > div > div > div > button {
        font-weight: bold;
    }

    /* 채팅 메시지 */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background: #f5f5f5;
        margin-right: 2rem;
    }
    
    /* 사이드바 너비 조정 (큰 화면에서만 적용) */
    @media (min-width: 992px) {
        [data-testid="stSidebar"] {
            min-width: 400px;
            max-width: 400px;
        }
    }
</style>
""", unsafe_allow_html=True)


# ===== 세션 상태 초기화 =====
@st.cache_resource
def get_agent(provider, api_key):
    """Agent 객체 생성 및 캐싱"""
    return DrugFoodAgent(provider=provider, api_key=api_key)

def init_session_state():
    """세션 상태 초기화"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    
    if 'provider' not in st.session_state:
        st.session_state.provider = "gemini"

    # Agent 초기화 (캐싱 사용)
    # API 키는 세션에 저장하지 않고 직접 전달 (보안)
    st.session_state.agent = get_agent(st.session_state.provider, GOOGLE_API_KEY)

    if 'messages' not in st.session_state:
        st.session_state.messages = []


init_session_state()


# ===== 데이터 로드 함수 =====
@st.cache_data
def load_drug_db():
    """약물 데이터베이스 로드"""
    try:
        df = pd.read_csv(APP_DIR / "../data/drugs.csv")
        return df
    except Exception as e:
        st.error(f"약물 DB 로드 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def load_interaction_db():
    """상호작용 데이터베이스 로드"""
    try:
        df = pd.read_csv(APP_DIR / "../data/drug_food_interactions.csv")
        return df
    except Exception as e:
        st.error(f"상호작용 DB 로드 실패: {e}")
        return pd.DataFrame()

def render_drug_db():
    """약물 DB 뷰어 렌더링"""
    st.header("💊 약물 데이터베이스 (Drug DB)")
    st.caption("약궁이 보유한 의약품 및 상호작용 데이터를 투명하게 공개합니다.")

    tab1, tab2 = st.tabs(["📋 의약품 목록", "⚠️ 상호작용 규칙"])

    with tab1:
        st.subheader("등록된 의약품 목록")
        df_drugs = load_drug_db()
        if not df_drugs.empty:
            # 검색 기능
            search_term = st.text_input("🔍 의약품 검색", placeholder="약물명 또는 성분명 입력")
            if search_term:
                df_drugs = df_drugs[
                    df_drugs['drug_name'].str.contains(search_term, case=False) | 
                    df_drugs['drug_ingredient'].str.contains(search_term, case=False)
                ]
            
            st.dataframe(
                df_drugs, 
                use_container_width=True,
                column_config={
                    "drug_id": "ID",
                    "drug_name": "약물명",
                    "drug_name": "약물명",
                    "manufacturer": "제조사",
                    "efficacy": "효능/효과",
                    "usage": "용법/용량",
                    "precautions": "주의사항",
                    "storage": "보관방법"
                }
            )
            st.caption(f"총 {len(df_drugs)}개의 의약품이 등록되어 있습니다.")
        else:
            st.info("등록된 의약품 데이터가 없습니다.")

    with tab2:
        st.subheader("약물-음식 상호작용 규칙")
        df_interactions = load_interaction_db()
        if not df_interactions.empty:
            # 필터링
            col1, col2 = st.columns(2)
            with col1:
                filter_drug = st.text_input("💊 약물 필터", placeholder="약물명 입력")
            with col2:
                filter_food = st.text_input("🍽️ 음식 필터", placeholder="음식명 입력")
            
            if filter_drug:
                df_interactions = df_interactions[df_interactions['drug_name'].str.contains(filter_drug, case=False)]
            if filter_food:
                df_interactions = df_interactions[df_interactions['food_name'].str.contains(filter_food, case=False)]

            st.dataframe(
                df_interactions,
                use_container_width=True,
                column_config={
                    "drug_name": "약물명",
                    "drug_ingredient": "성분명",
                    "drug_category": "약물 분류",
                    "food_name": "음식명",
                    "food_category": "음식 분류",
                    "risk_level": st.column_config.SelectboxColumn(
                        "위험도",
                        options=["safe", "caution", "danger"],
                        help="safe: 안전, caution: 주의, danger: 위험"
                    ),
                    "interaction_mechanism": "상호작용 기전",
                    "clinical_effect": "임상적 효과",
                    "recommendation": "권장사항",
                    "alternative_food": "대체 음식",
                    "source": "출처"
                }
            )
            st.caption(f"총 {len(df_interactions)}개의 상호작용 규칙이 등록되어 있습니다.")
        else:
            st.info("등록된 상호작용 데이터가 없습니다.")

# ===== 사이드바 =====
def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        # LLM 제공자 설정 (Hidden)
        # Gemini로 고정됨
        if st.session_state.provider != "gemini":
             st.session_state.provider = "gemini"
             st.session_state.api_key = GOOGLE_API_KEY
             st.rerun()
        
        # 내 약물 관리
        st.markdown("## 💊 내 약물 관리")
        
        # 약물 데이터 로드 (캐싱)
        @st.cache_data
        def load_drug_list():
            try:
                # 상호작용 정보가 있는 약물만 로드 (사용자 요청 반영)
                interactions_df = pd.read_csv(APP_DIR / "../data/drug_food_interactions.csv")
                # 중복 제거 및 정렬
                return sorted(interactions_df['drug_name'].unique().tolist())
            except Exception as e:
                st.error(f"약물 목록 로드 실패: {e}")
                return []

        drug_list = load_drug_list()
        
        # 약물 등록 폼
        with st.form("drug_form", clear_on_submit=True, enter_to_submit=False):
            # 자동완성을 위한 selectbox (입력 가능)
            drug_name = st.selectbox(
                "약물명 검색", 
                options=[""] + drug_list, # 빈 옵션 추가
                placeholder="약물명을 입력하거나 선택하세요",
                index=0
            )
            
            # drug_category는 AI가 자동 분류
            dosage = st.text_input("복용량 (선택)", placeholder="예: 5mg 1일 1회")
            
            submitted = st.form_submit_button("➕ 약물 등록", use_container_width=True)
            
            if submitted:
                if not drug_name:
                    st.warning("약물명을 선택하거나 입력해주세요.")
                else:
                    with st.spinner("약물 분류를 확인 중입니다..."):
                        drug_category = st.session_state.agent.categorize_drug(drug_name)
                    
                    if drug_category.startswith("Error:"):
                        st.error(f"⚠️ 분류 오류: {drug_category}")
                        drug_category = "기타"
                    
                    result = st.session_state.agent.user_db.register_drug(
                        user_id=st.session_state.user_id,
                        drug_name=drug_name,
                        drug_category=drug_category,
                        dosage=dosage if dosage else None
                    )
                    if result['success']:
                        st.success(f"✅ {drug_name} ({drug_category}) 등록 완료!")
                        # st.rerun() 제거: 메시지가 유지되도록 함. 
                        # 목록은 아래에서 렌더링되므로 자동으로 업데이트됨.
                    else:
                        st.error(result['message'])
        
        # 등록된 약물 목록
        st.markdown("### 📋 등록된 약물")
        drugs = st.session_state.agent.user_db.get_user_drugs(st.session_state.user_id)
        
        if drugs:
            for drug in drugs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    label = drug['drug_name']
                    if drug.get('drug_category'):
                        label += f" ({drug['drug_category']})"
                    st.markdown(f"**💊 {label}**")
                    if drug.get('dosage'):
                        st.caption(drug['dosage'])
                with col2:
                    if st.button("🗑️", key=f"del_{drug['drug_name']}", help="삭제"):
                        st.session_state.agent.user_db.remove_drug(
                            st.session_state.user_id, 
                            drug['drug_name']
                        )
                        st.rerun()
            
            # 전체 삭제
            if st.button("🗑️ 전체 삭제", use_container_width=True):
                st.session_state.agent.user_db.clear_user_drugs(st.session_state.user_id)
                st.rerun()
        else:
            st.info("등록된 약물이 없습니다.\n약물을 등록하면 맞춤 상담이 가능합니다.")
        
        st.divider()
        
        # 통계
        st.markdown("## 📊 데이터베이스 정보")
        stats = st.session_state.agent.rag.get_stats()
        st.metric("총 상호작용 데이터", f"{stats['total_interactions']}건")
        st.metric("약물 종류", f"{stats['drugs']}종")
        st.metric("음식 종류", f"{stats['foods']}종")
        
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()


# ===== 빠른 확인 탭 =====
def render_quick_check():
    """빠른 상호작용 확인"""
    # 카테고리 버튼
    st.markdown("### 🔍 빠른 상호작용 확인")
    st.caption("스타벅스 커피, 치킨, 김치찌개 등 음식명을 입력해 상호작용을 확인할 수 있습니다.")
    
    st.markdown("**사용되는 음식:**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    categories = [
        ("🍎 과일", "과일"),
        ("🥦 채소", "채소"),
        ("🥩 고기/생선", "고기"),
        ("🥛 유제품", "유제품"),
        ("🌿 기타", "기타")
    ]
    
    selected_category = None
    for col, (label, category) in zip([col1, col2, col3, col4, col5], categories):
        with col:
            if st.button(label, use_container_width=True):
                selected_category = category

    # 검색바 스타일 입력
    col1, col2 = st.columns([4, 1])
    with col1:
        food_input = st.text_input(
            "음식명 입력",
            placeholder="친구들과 먹고 싶은데 나는 치킨 먹어도 돼요?",
            label_visibility="collapsed"
        )
    with col2:
        check_button = st.button("확인", type="primary", use_container_width=True)
    
    # 확인 실행 (카테고리 선택 시 해당 카테고리 대표 음식 예시로 확인)
    food_to_check = None
    if selected_category:
        # 카테고리별 예시 음식 매핑
        examples = {
            "과일": "자몽",
            "채소": "시금치",
            "고기": "소고기",
            "유제품": "우유",
            "기타": "커피"
        }
        food_to_check = examples.get(selected_category)
        st.info(f"💡 '{selected_category}' 카테고리 예시로 '{food_to_check}'을(를) 확인합니다.")
    elif check_button and food_input:
        food_to_check = food_input
    
    if food_to_check:
        result = st.session_state.agent.check_interaction(
            st.session_state.user_id,
            food_to_check
        )
        
        # 결과 표시
        st.markdown("---")
        
        # 추출된 음식명 표시
        extracted_food = result.get('extracted_food', food_to_check)
        if extracted_food != food_to_check:
             st.info(f"💡 '{food_to_check}'에서 '{extracted_food}'(으)로 확인했습니다.")
        
        
        if result['danger_count'] > 0:
            st.markdown(f"""
            <div class="risk-danger">
                <h3>🔴 위험!</h3>
                <p>{result['message']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif result['warning_count'] > 0:
            st.markdown(f"""
            <div class="risk-warning">
                <h3>🟠 주의 필요</h3>
                <p>{result['message']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif result['interactions']:
            st.markdown(f"""
            <div class="risk-caution">
                <h3>🟡 확인 필요</h3>
                <p>{result['message']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="risk-safe">
                <h3>🟢 안전</h3>
                <p>{result['message']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 상세 정보
        if result['interactions']:
            st.markdown("#### 📋 상세 정보")
            for inter in result['interactions']:
                risk_class = f"risk-{inter['risk_level']}"
                # XSS 방지: HTML escape 처리
                safe_drug_name = html.escape(str(inter['drug_name']))
                safe_food_name = html.escape(str(inter['food_name']))
                safe_recommendation = html.escape(str(inter['recommendation']))
                safe_alternative = html.escape(str(inter.get('alternative', '')))

                alternative_text = ""
                if inter.get('alternative') and str(inter['alternative']).lower() != 'nan':
                    alternative_text = f"🔄 대안: {safe_alternative}<br>"

                st.markdown(f"""
                <div class="{risk_class}">
                    <strong>{inter['risk_emoji']} {safe_drug_name} + {safe_food_name}</strong><br>
                    ➡️ {safe_recommendation}<br>
                    {alternative_text}
                </div>
                """, unsafe_allow_html=True)


# ===== AI 상담 탭 =====
def render_chat():
    """AI 채팅 인터페이스"""
    st.markdown("### 💬 AI 상담")
    st.caption("약물-음식 상호작용에 대해 자유롭게 질문하세요.")
    
    # 예시 질문
    with st.expander("💡 예시 질문"):
        examples = [
            "자몽 먹어도 되나요?",
            "술 마셔도 괜찮을까요?",
            "피해야 할 음식이 뭐가 있나요?",
            "커피는 언제 마셔도 되나요?",
            "비타민과 함께 먹어도 되나요?"
        ]
        for ex in examples:
            if st.button(f"📝 {ex}", key=f"ex_{ex}"):
                st.session_state.messages.append({"role": "user", "content": ex})
                
                # AI 응답
                with st.spinner("답변 생성 중..."):
                    response = st.session_state.agent.chat(
                        st.session_state.user_id,
                        ex
                    )
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response['response']
                })
                st.rerun()
    
    # 채팅 기록 표시
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 나</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 약궁 (YakGung)</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # 입력 폼
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "메시지 입력",
            placeholder="질문을 입력하세요...",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([5, 1])
        with col2:
            submitted = st.form_submit_button("전송", use_container_width=True)
        
        if submitted and user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # AI 응답
            with st.spinner("답변 생성 중..."):
                response = st.session_state.agent.chat(
                    st.session_state.user_id,
                    user_input
                )
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response['response']
            })
            st.rerun()
    
    # 대화 초기화
    if st.session_state.messages:
        if st.button("🗑️ 대화 내역 삭제"):
            st.session_state.messages = []
            st.session_state.agent.clear_history()
            st.rerun()


# ===== 주의 음식 탭 =====
def render_warnings():
    """주의 음식 목록"""
    st.markdown("### ⚠️ 주의해야 할 음식")
    
    drugs = st.session_state.agent.user_db.get_user_drugs(st.session_state.user_id)
    
    if not drugs:
        st.info("💊 약물을 먼저 등록해주세요.\n왼쪽 사이드바에서 복용 중인 약물을 등록하면 주의 음식 목록을 확인할 수 있습니다.")
        return
    
    warnings = st.session_state.agent.get_all_warnings(st.session_state.user_id)
    
    if not warnings:
        st.success("🎉 등록된 약물에 대해 특별히 주의할 음식이 없습니다.")
        return
    
    # 위험도별 분류
    danger_items = [w for w in warnings if w['risk_level'] == 'danger']
    warning_items = [w for w in warnings if w['risk_level'] == 'warning']
    
    if danger_items:
        st.markdown("#### 🔴 절대 금기 음식")
        for item in danger_items:
            # XSS 방지: HTML escape 처리
            safe_drug_name = html.escape(str(item['drug_name']))
            safe_food_name = html.escape(str(item['food_name']))
            safe_recommendation = html.escape(str(item['recommendation']))
            st.markdown(f"""
            <div class="risk-danger">
                <strong>💊 {safe_drug_name}</strong> + <strong>🍽️ {safe_food_name}</strong><br>
                ➡️ {safe_recommendation}
            </div>
            """, unsafe_allow_html=True)
    
    if warning_items:
        st.markdown("#### 🟠 주의 필요 음식")
        for item in warning_items:
            # XSS 방지: HTML escape 처리
            safe_drug_name = html.escape(str(item['drug_name']))
            safe_food_name = html.escape(str(item['food_name']))
            safe_recommendation = html.escape(str(item['recommendation']))
            st.markdown(f"""
            <div class="risk-warning">
                <strong>💊 {safe_drug_name}</strong> + <strong>🍽️ {safe_food_name}</strong><br>
                ➡️ {safe_recommendation}
            </div>
            """, unsafe_allow_html=True)


# ===== 메인 =====
def render_landing_page():
    """랜딩 페이지 렌더링"""
    # 화면 전환 시 잔상 제거를 위한 컨테이너
    landing_container = st.empty()
    
    with landing_container.container():
        st.markdown("""
        <style>
        :root {
            --primary: #0A1628;
            --secondary: #1E3A5F;
            --accent: #00D4AA;
            --accent-glow: #00FFD1;
            --warning: #FFB800;
            --danger: #FF4757;
            --safe: #00D4AA;
            --caution: #FFA502;
            --text: #E8F4F8;
            --text-muted: #8BA4B4;
            --card-bg: rgba(30, 58, 95, 0.4);
            --glass: rgba(255, 255, 255, 0.05);
        }

        .landing-container {
            font-family: 'Noto Sans KR', sans-serif;
            color: var(--text);
            background-color: var(--primary);
            padding-bottom: 5rem;
        }

        .landing-container h1, .landing-container h2, .landing-container h3 {
            color: var(--text);
        }

        /* Hero Section */
        .hero {
            text-align: center;
            padding: 6rem 1rem 4rem;
            background: radial-gradient(ellipse at 50% 50%, rgba(30, 58, 95, 0.3) 0%, var(--primary) 70%);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1.2rem;
            background: var(--glass);
            border: 1px solid rgba(0, 212, 170, 0.3);
            border-radius: 50px;
            font-size: 0.85rem;
            color: var(--accent);
            margin-bottom: 2rem;
        }

        .hero h1 {
            font-size: 4rem;
            font-weight: 900;
            margin-bottom: 1.5rem;
            line-height: 1.1;
        }

        .highlight {
            background: linear-gradient(135deg, var(--accent), var(--accent-glow));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            font-size: 1.3rem;
            color: var(--text-muted);
            max-width: 700px;
            margin: 0 auto 3rem;
            line-height: 1.6;
        }

        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 4rem;
            flex-wrap: wrap;
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        .stat-label {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-top: 0.3rem;
        }

        /* Section Styles */
        .section {
            padding: 5rem 1rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }

        .section-number {
            font-family: monospace;
            font-size: 0.9rem;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }

        .section-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .section-desc {
            color: var(--text-muted);
            max-width: 600px;
            margin: 0 auto;
        }

        /* Cards */
        .card {
            background: var(--card-bg);
            border: 1px solid rgba(0, 212, 170, 0.1);
            border-radius: 20px;
            padding: 2rem;
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: rgba(0, 212, 170, 0.3);
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        /* Overview Grid */
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .overview-icon {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
        }

        .overview-card h3 {
            font-size: 1.2rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .overview-card p {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Problem List */
        .problem-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }

        .problem-item {
            display: flex;
            gap: 1.5rem;
            align-items: flex-start;
            padding: 1.5rem;
            background: var(--card-bg);
            border-radius: 16px;
            border-left: 4px solid var(--danger);
        }

        .problem-item-icon {
            font-size: 1.5rem;
            min-width: 50px;
            height: 50px;
            background: rgba(255, 71, 87, 0.2);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .problem-item h4 {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--text);
        }

        .problem-item p {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin: 0;
        }

        /* Features */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
        }

        .feature-card {
            padding: 1.5rem;
            background: var(--card-bg);
            border-radius: 16px;
            border: 1px solid rgba(0, 212, 170, 0.1);
        }

        .feature-number {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent), #007A5E);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #fff;
        }

        .feature-priority {
            display: inline-block;
            margin-top: 1rem;
            font-size: 0.8rem;
            color: var(--accent);
        }

        /* Effects */
        .effects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .effect-item {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            align-items: flex-start;
        }

        .effect-icon {
            font-size: 1.5rem;
            min-width: 40px;
            text-align: center;
        }
        
        /* Streamlit Button Override */
        .stButton button {
            width: 100%;
            border-radius: 50px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1.1rem;
            margin-top: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Hero Section
        st.markdown("""
            <div class="landing-container">
                <div class="hero">
                    <div class="badge">Health & Wellness RAG Agent AI</div>
                    <h1><span class="highlight">DrugFood</span> Guard</h1>
                    <p class="hero-subtitle">
                        복용 중인 약물과 음식 간의 상호작용 위험을 실시간으로 분석하여<br>
                        안전한 복약 생활을 지원하는 <strong>RAG 기반 AI Agent</strong>
                    </p>
                    <div class="hero-stats">
                        <div class="stat">
                            <div class="stat-value">1,500만+</div>
                            <div class="stat-label">만성질환 복약자</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">6.5개</div>
                            <div class="stat-label">65세 이상 평균 복용약</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">30%</div>
                            <div class="stat-label">약물 부작용 중 상호작용</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 약궁 시작하기", key="hero_start", type="primary", use_container_width=True):
                landing_container.empty() # 즉시 비우기
                st.session_state.show_landing = False
                st.rerun()

        # Overview Section
        st.markdown("""
            <div class="landing-container">
                <div class="section">
                    <div class="section-header">
                        <div class="section-number">01</div>
                        <h2 class="section-title">Project Overview</h2>
                        <p class="section-desc">프로젝트의 목적, 핵심 문제, 기대 효과</p>
                    </div>
                    <div class="overview-grid">
                        <div class="card overview-card">
                            <div class="overview-icon">🎯</div>
                            <h3>목적 (Purpose)</h3>
                            <p>복용 중인 약물과 섭취하려는 음식/음료/건강기능식품 간의 상호작용 위험을 실시간으로 분석하여, 안전한 복약 생활을 지원하는 AI Agent 개발</p>
                        </div>
                        <div class="card overview-card">
                            <div class="overview-icon">⚡</div>
                            <h3>핵심 문제 (Core Problem)</h3>
                            <p>다약제 복용자가 증가하는 고령화 사회에서, 약-음식 상호작용에 대한 정보 접근성이 낮아 부작용 위험에 무방비로 노출됨</p>
                        </div>
                        <div class="card overview-card">
                            <div class="overview-icon">✨</div>
                            <h3>기대 효과 (Expected Effects)</h3>
                            <p>약물 부작용 사전 예방, 복약 순응도 향상, 불필요한 응급실 방문 감소, 의료비 절감 및 삶의 질 개선</p>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Problem Section
        st.markdown("""
            <div class="landing-container">
                <div class="section">
                    <div class="section-header">
                        <div class="section-number">02</div>
                        <h2 class="section-title">Why DrugFood Guard?</h2>
                        <p class="section-desc">일상 속 숨겨진 위험을 찾아냅니다</p>
                    </div>
                    <div class="problem-list">
                        <div class="problem-item">
                            <div class="problem-item-icon">📊</div>
                            <div>
                                <h4>다약제 복용의 일상화</h4>
                                <p>65세 이상 노인 평균 6.5개 약물 복용. 복용 약물이 많을수록 상호작용 위험이 기하급수적으로 증가합니다.</p>
                            </div>
                        </div>
                        <div class="problem-item">
                            <div class="problem-item-icon">🔍</div>
                            <div>
                                <h4>정보 접근성의 한계</h4>
                                <p>약사 상담은 시간 부족, 인터넷 검색은 신뢰도 불확실, 기존 앱은 약-약 상호작용만 제공합니다.</p>
                            </div>
                        </div>
                        <div class="problem-item">
                            <div class="problem-item-icon">⚠️</div>
                            <div>
                                <h4>실제 피해 사례</h4>
                                <p>와파린+청국장(약효 감소), 스타틴+자몽(농도 급상승), 항생제+유제품(흡수 저하) 등 심각한 부작용 발생</p>
                            </div>
                        </div>
                        <div class="problem-item">
                            <div class="problem-item-icon">🤖</div>
                            <div>
                                <h4>AI Agent의 필요성</h4>
                                <p>복합 데이터 분석, 개인 맞춤 판단, 자연어 질의 대응, 실시간 최신 정보 반영이 필요합니다.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Features (MVP) Section
        st.markdown("""
            <div class="landing-container">
                <div class="section">
                    <div class="section-header">
                        <div class="section-number">03</div>
                        <h2 class="section-title">Key Features</h2>
                        <p class="section-desc">안전한 복약 생활을 위한 핵심 기능</p>
                    </div>
                    <div class="feature-grid">
                        <div class="feature-card">
                            <div class="feature-number">F1</div>
                            <h4>복용약 등록</h4>
                            <p>약 이름을 검색하여 내 약통에 저장하고 관리합니다.</p>
                            <span class="feature-priority">★★★ 필수</span>
                        </div>
                        <div class="feature-card">
                            <div class="feature-number">F2</div>
                            <h4>음식 상호작용 체크</h4>
                            <p>"이거 먹어도 돼?" 질문에 위험도와 이유를 설명합니다.</p>
                            <span class="feature-priority">★★★ 필수</span>
                        </div>
                        <div class="feature-card">
                            <div class="feature-number">F3</div>
                            <h4>안전한 대안 제시</h4>
                            <p>위험 판정 시 대신 섭취 가능한 안전한 음식을 추천합니다.</p>
                            <span class="feature-priority">★★☆ 권장</span>
                        </div>
                        <div class="feature-card">
                            <div class="feature-number">F4</div>
                            <h4>주의사항 알림</h4>
                            <p>약 복용 시 피해야 할 생활 습관과 주의사항을 안내합니다.</p>
                            <span class="feature-priority">★★☆ 권장</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Effects Section
        st.markdown("""
            <div class="landing-container">
                <div class="section">
                    <div class="section-header">
                        <div class="section-number">04</div>
                        <h2 class="section-title">Benefits</h2>
                        <p class="section-desc">DrugFood Guard가 가져올 변화</p>
                    </div>
                    <div class="effects-grid">
                        <div class="card">
                            <h3>✨ 기대효과</h3>
                            <br>
                            <div class="effect-item">
                                <div class="effect-icon">🛡️</div>
                                <div>
                                    <h4>약물 부작용 사전 예방</h4>
                                    <p>상호작용 위험을 미리 인지하여 부작용 발생 감소</p>
                                </div>
                            </div>
                            <div class="effect-item">
                                <div class="effect-icon">💊</div>
                                <div>
                                    <h4>복약 순응도 향상</h4>
                                    <p>안전한 식사 가이드로 약 복용 지속률 증가</p>
                                </div>
                            </div>
                            <div class="effect-item">
                                <div class="effect-icon">🏥</div>
                                <div>
                                    <h4>의료비 절감</h4>
                                    <p>불필요한 응급실 방문 및 입원 감소</p>
                                </div>
                            </div>
                        </div>
                        <div class="card" style="border-color: var(--danger);">
                            <h3 style="color: var(--danger);">⚠️ 한계 및 면책</h3>
                            <br>
                            <div class="effect-item">
                                <div class="effect-icon">⚖️</div>
                                <div>
                                    <h4>의료 조언 한계</h4>
                                    <p>본 서비스는 정보 제공 목적이며, 의학적 진단을 대체하지 않습니다.</p>
                                </div>
                            </div>
                            <div class="effect-item">
                                <div class="effect-icon">👤</div>
                                <div>
                                    <h4>개인차 미반영</h4>
                                    <p>개인의 특이 체질이나 기저질환에 따라 결과가 다를 수 있습니다.</p>
                                </div>
                            </div>
                            <div class="effect-item">
                                <div class="effect-icon">📊</div>
                                <div>
                                    <h4>참고용 정보</h4>
                                    <p>최종 판단은 반드시 의사나 약사와 상담해야 합니다.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # CTA Section
        st.markdown("""
            <div class="landing-container">
                <div class="section" style="text-align: center;">
                    <h2 class="section-title">Ready to Start?</h2>
                    <p class="section-desc" style="margin-bottom: 2rem;">
                        지금 바로 DrugFood Guard와 함께 안전한 복약 생활을 시작하세요.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 서비스 시작하기", key="cta_start", type="primary", use_container_width=True):
                landing_container.empty() # 즉시 비우기
                st.session_state.show_landing = False
                st.rerun()
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)

def main():
    """메인 애플리케이션"""
    # 랜딩 페이지 표시 여부 확인
    if 'show_landing' not in st.session_state:
        st.session_state.show_landing = True
    
    if st.session_state.show_landing:
        render_landing_page()
        return

    # ===== 인증 (Authentication) =====
    config = None
    
    # 1. Streamlit Secrets에서 로드 시도 (배포 환경)
    if "credentials" in st.secrets:
        config = {
            "credentials": st.secrets["credentials"].to_dict(),
            "cookie": st.secrets["cookie"].to_dict(),
            "preauthorized": st.secrets["preauthorized"].to_dict() if "preauthorized" in st.secrets else {'emails': []}
        }
    
    # 2. 로컬 파일에서 로드 시도 (개발 환경)
    if not config:
        try:
            with open(APP_DIR / '../auth_config.yaml') as file:
                config = yaml.load(file, Loader=SafeLoader)
        except FileNotFoundError:
            pass
            
    if not config:
        # 비상용 기본 설정
        st.warning("⚠️ 인증 설정이 없어 기본 데모 계정으로 실행됩니다. (admin / 1234)")
        config = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "email": "admin@example.com",
                        "name": "Admin",
                        "password": "$2b$12$qbGyuPnyvDaP1D7quPK36.bYGSFNWkqZS9wZExFpE3/Kc/IhdIefG" # 1234
                    }
                }
            },
            "cookie": {
                "name": "drugfood_guard_cookie",
                "key": "random_signature_key",
                "expiry_days": 30
            },
            "preauthorized": {"emails": []}
        }

    # 3. DB에서 사용자 정보 로드 및 병합 (Persistence 보장)
    try:
        # 임시 Agent 생성하여 DB 접근 (아직 로그인 전이라 session_state.agent가 없을 수 있음)
        temp_db = UserDrugDB() 
        
        # Admin 계정이 DB에 없으면 자동 생성 (Cloud 배포 시 초기화 대응)
        admin_id = "admin"
        if not temp_db.get_user(admin_id):
            # 1234
            default_pw_hash = "$2b$12$qbGyuPnyvDaP1D7quPK36.bYGSFNWkqZS9wZExFpE3/Kc/IhdIefG" 
            temp_db.create_user(admin_id, "admin@example.com", "Admin", default_pw_hash)
            print("Default admin user created in DB.")

        db_users = temp_db.get_all_users()
        
        if db_users:
            # 기존 config에 DB 사용자 병합
            if 'credentials' not in config:
                config['credentials'] = {'usernames': {}}
            if 'usernames' not in config['credentials']:
                config['credentials']['usernames'] = {}
                
            config['credentials']['usernames'].update(db_users)
    except Exception as e:
        st.error(f"DB 사용자 로드 실패: {e}")

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # 로그인 위젯을 담을 컨테이너 (로그인 성공 시 제거하기 위해)
    login_container = st.empty()
    
    with login_container:
        authenticator.login(location='main')

    if st.session_state["authentication_status"] is False:
        st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
    elif st.session_state["authentication_status"] is None:
        st.warning('아이디와 비밀번호를 입력하세요.')
    
    if st.session_state["authentication_status"]:
        # 로그인 성공 시 로그인 위젯 컨테이너 비우기 (화면 전환 속도 개선)
        login_container.empty()
    else:
        # 로그인 실패/미로그인 시 회원가입 폼 표시
        with st.expander("회원가입 (Register)", expanded=False):
            with st.form("register_form"):
                new_username = st.text_input("아이디 (Username)")
                new_password = st.text_input("비밀번호 (Password)", type="password")
                new_password_repeat = st.text_input("비밀번호 확인 (Repeat Password)", type="password")
                
                # 면책 조항 동의
                with st.expander("⚠️ 이용 약관 및 면책 조항 (필수 확인)", expanded=False):
                    st.markdown("""
                    **1. 의학적 조언 아님**: 본 서비스는 정보 제공 목적이며, 의사의 진단을 대체하지 않습니다.
                    **2. 책임의 제한**: 서비스 이용에 따른 결과에 대해 제공자는 법적 책임을 지지 않습니다.
                    **3. 응급 상황**: 응급 시 즉시 119에 연락하거나 병원을 방문하세요.
                    """)
                agree_disclaimer = st.checkbox("위 약관에 동의합니다.")
                
                submit_button = st.form_submit_button("가입하기")

                if submit_button:
                    if not agree_disclaimer:
                        st.error("약관에 동의해야 가입할 수 있습니다.")
                    elif new_username and new_password:
                        if new_password != new_password_repeat:
                            st.error("비밀번호가 일치하지 않습니다.")
                        elif new_username in config['credentials']['usernames']:
                            st.error("이미 존재하는 아이디입니다.")
                        else:
                            # 비밀번호 해싱
                            hashed_password = Hasher().hash(new_password)
                            
                            # 새 사용자 정보 생성 (이메일/이름은 아이디와 동일하게 설정)
                            new_user_info = {
                                'email': f"{new_username}@example.com",
                                'name': new_username,
                                'password': hashed_password
                            }
                            
                            # Config 업데이트 (메모리)
                            config['credentials']['usernames'][new_username] = new_user_info
                            
                            # DB에 영구 저장 (Cloud 환경 대응)
                            try:
                                temp_db = UserDrugDB()
                                temp_db.create_user(
                                    user_id=new_username,
                                    email=new_user_info['email'],
                                    name=new_user_info['name'],
                                    password=hashed_password
                                )
                                st.success("회원가입 성공! (DB 저장 완료)")
                            except Exception as e:
                                st.error(f"DB 저장 실패: {e}")

                            # 로컬 파일 저장 시도 (선택적)
                            try:
                                with open(APP_DIR / '../auth_config.yaml', 'w') as file:
                                    yaml.dump(config, file, default_flow_style=False)
                            except Exception:
                                # Cloud 환경 등 파일 쓰기가 불가능한 경우 무시 (DB에 저장했으므로)
                                pass
                                
                            st.info("이제 로그인해주세요.")
                    else:
                        st.warning("모든 필드를 입력해주세요.")
        return
    
    # 로그인 성공 시 사이드바에 로그아웃 버튼 표시
    with st.sidebar:
        st.write(f"환영합니다, **{st.session_state['name']}**님! 👋")
        def logout_callback(*args, **kwargs):
            st.session_state.show_landing = True

        authenticator.logout(location='sidebar', callback=logout_callback) # 로그아웃 버튼 위치 지정 및 콜백
        st.divider()
    
    # 사용자 ID를 로그인한 사용자로 설정 (데이터 개인화)
    st.session_state.user_id = st.session_state["username"]
    # 헤더
    # 헤더 (배너 스타일)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-header-title">💊 약궁 (YakGung)</div>
            <div class="main-header-subtitle">약과 음식 상호작용을 확인하고 안전하게 복용하세요</div>
        </div>
    """, unsafe_allow_html=True)
    

    
    # 사이드바
    render_sidebar()
    
    # API 키 확인
    if not GOOGLE_API_KEY:
        st.error("⚠️ Google API Key가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        st.info("💡 [Google AI Studio](https://aistudio.google.com/apikey)에서 무료 API 키를 발급받아 .env 파일의 GOOGLE_API_KEY에 입력하세요.")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 빠른 확인", "💬 AI 상담", "⚠️ 주의 음식", "💊 약물 DB"])
    
    with tab1:
        render_quick_check()
    
    with tab2:
        render_chat()
    
    with tab3:
        render_warnings()
        
    with tab4:
        render_drug_db()
    
    # 푸터
    st.markdown("---")
    st.caption("""
    ⚠️ **주의사항**: 이 서비스는 참고용 정보를 제공하며, 의학적 조언을 대체하지 않습니다.
    정확한 정보는 반드시 의사 또는 약사와 상담하세요.
    
    📚 데이터 출처: FDA Drug Interactions Guide, 식약처 DUR, DrugBank, 약학정보원
    """)


if __name__ == "__main__":
    main()
