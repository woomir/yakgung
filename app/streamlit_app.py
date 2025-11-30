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

    # API 키 업데이트 (Secrets 변경 사항 반영)
    st.session_state.api_key = GOOGLE_API_KEY

    # Agent 초기화 (캐싱 사용)
    # API 키가 변경되면 새로운 Agent 생성
    st.session_state.agent = get_agent(st.session_state.provider, st.session_state.api_key)

    if 'messages' not in st.session_state:
        st.session_state.messages = []


init_session_state()


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
                drugs_df = pd.read_csv(APP_DIR / "../data/drugs.csv")
                return drugs_df['drug_name'].tolist()
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
                st.markdown(f"""
                <div class="{risk_class}">
                    <strong>{inter['risk_emoji']} {inter['drug_name']} + {inter['food_name']}</strong><br>
                    ➡️ {inter['recommendation']}<br>
                    {"🔄 대안: " + inter['alternative'] if inter.get('alternative') and inter['alternative'] != 'nan' else ""}
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
            st.markdown(f"""
            <div class="risk-danger">
                <strong>💊 {item['drug_name']}</strong> + <strong>🍽️ {item['food_name']}</strong><br>
                ➡️ {item['recommendation']}
            </div>
            """, unsafe_allow_html=True)
    
    if warning_items:
        st.markdown("#### 🟠 주의 필요 음식")
        for item in warning_items:
            st.markdown(f"""
            <div class="risk-warning">
                <strong>💊 {item['drug_name']}</strong> + <strong>🍽️ {item['food_name']}</strong><br>
                ➡️ {item['recommendation']}
            </div>
            """, unsafe_allow_html=True)


# ===== 메인 =====
def main():
    """메인 애플리케이션"""
    # ===== 인증 (Authentication) =====
    try:
        with open(APP_DIR / '../auth_config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("인증 설정 파일(auth_config.yaml)을 찾을 수 없습니다.")
        return

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    authenticator.login(location='main')

    if st.session_state["authentication_status"] is False:
        st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
        return
    elif st.session_state["authentication_status"] is None:
        st.warning('아이디와 비밀번호를 입력하세요.')
        return
    
    # 로그인 성공 시 사이드바에 로그아웃 버튼 표시
    with st.sidebar:
        st.write(f"환영합니다, **{st.session_state['name']}**님! 👋")
        authenticator.logout(location='sidebar') # 로그아웃 버튼 위치 지정
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
    
    # ===== 면책 조항 (Liability Disclaimer) =====
    if 'disclaimer_agreed' not in st.session_state:
        st.session_state.disclaimer_agreed = False
        
    if not st.session_state.disclaimer_agreed:
        with st.expander("⚠️ 서비스 이용 약관 및 면책 조항 (필수)", expanded=True):
            st.markdown("""
            ### ⚖️ 법적 고지 및 면책 조항 (Legal Disclaimer)
            
            **본 서비스 '약궁(YakGung)'을 이용하기 전에 아래 내용을 반드시 확인하시기 바랍니다.**
            
            #### 1. 의학적 조언 아님 (No Medical Advice)
            본 서비스가 제공하는 모든 정보(텍스트, 데이터, 그래픽 등)는 **일반적인 정보 제공 및 교육 목적**으로만 제공됩니다. 이는 의사, 약사 등 보건의료 전문가의 전문적인 의학적 조언, 진단, 치료를 대체할 수 없습니다.
            
            #### 2. 의사-환자 관계 부존재 (No Doctor-Patient Relationship)
            본 서비스의 사용은 사용자와 서비스 제공자 간의 의사-환자 관계를 형성하지 않습니다. 건강상의 문제나 의문 사항이 있을 경우, 반드시 **자격 있는 의료 전문가와 상담**하십시오.
            
            #### 3. 정보의 정확성 및 한계 (Accuracy and Limitations)
            *   본 서비스는 식약처(MFDS), FDA 등 공신력 있는 기관의 공개 데이터와 AI 기술을 기반으로 정보를 제공하지만, 모든 약물 상호작용과 최신 의학 정보를 포괄한다고 보장할 수 없습니다.
            *   AI 모델(LLM)의 특성상 부정확하거나 시의적절하지 않은 정보가 생성될 가능성이 있습니다.
            
            #### 4. 응급 상황 (Medical Emergencies)
            본 서비스는 응급 의료 상황을 위해 설계되지 않았습니다. 응급 상황이 발생하거나 의심되는 경우, 즉시 **119**에 연락하거나 가까운 응급실을 방문하십시오.
            
            #### 5. 책임의 제한 (Limitation of Liability)
            사용자는 본 서비스의 정보를 바탕으로 내린 결정에 대해 전적으로 책임을 집니다. 서비스 제공자는 본 서비스 사용으로 인해 발생한 어떠한 직접적, 간접적, 부수적 피해에 대해서도 법적 책임을 지지 않습니다.
            """)
            
            st.markdown("---")
            agree = st.checkbox("위 '법적 고지 및 면책 조항'을 모두 읽었으며, 이에 동의합니다.")
            
            if agree:
                if st.button("서비스 시작하기", type="primary", use_container_width=True):
                    st.session_state.disclaimer_agreed = True
                    st.rerun()
            
            # 동의 버튼을 누르기 전까지는 무조건 중단
            st.warning("서비스를 이용하려면 위 약관에 동의하고 '서비스 시작하기' 버튼을 눌러주세요.")
            st.stop()
    
    # 사이드바
    render_sidebar()
    
    # API 키 확인
    if not st.session_state.api_key:
        st.error("⚠️ Google API Key가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        st.info("💡 [Google AI Studio](https://aistudio.google.com/apikey)에서 무료 API 키를 발급받아 .env 파일의 GOOGLE_API_KEY에 입력하세요.")
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["🔍 빠른 확인", "💬 AI 상담", "⚠️ 주의 음식"])
    
    with tab1:
        render_quick_check()
    
    with tab2:
        render_chat()
    
    with tab3:
        render_warnings()
    
    # 푸터
    st.markdown("---")
    st.caption("""
    ⚠️ **주의사항**: 이 서비스는 참고용 정보를 제공하며, 의학적 조언을 대체하지 않습니다.
    정확한 정보는 반드시 의사 또는 약사와 상담하세요.
    
    📚 데이터 출처: FDA Drug Interactions Guide, 식약처 DUR, DrugBank, 약학정보원
    """)


if __name__ == "__main__":
    main()
