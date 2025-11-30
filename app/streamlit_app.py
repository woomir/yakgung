"""
DrugFood Guard - Streamlit Application
약궁 (YakGung) - 약물-음식 상호작용 확인 AI Agent
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import uuid

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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a5f;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .drug-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
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
    .stButton > button {
        width: 100%;
    }
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
def init_session_state():
    """세션 상태 초기화"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    
    if 'provider' not in st.session_state:
        st.session_state.provider = "gemini"

    # API 키 업데이트 (Secrets 변경 사항 반영)
    st.session_state.api_key = GOOGLE_API_KEY

    # Agent 초기화 조건:
    # 1. Agent가 없거나
    # 2. API 키가 변경되었거나 (Agent가 가진 키와 현재 키 불일치)
    # 3. categorize_drug 메서드가 없는 경우 (구버전 객체)
    should_reinit = False
    if 'agent' not in st.session_state:
        should_reinit = True
    elif getattr(st.session_state.agent, 'api_key', None) != st.session_state.api_key:
        should_reinit = True
    elif not hasattr(st.session_state.agent, 'categorize_drug'):
        should_reinit = True

    if should_reinit:
        st.session_state.agent = DrugFoodAgent(
            provider=st.session_state.provider,
            api_key=st.session_state.api_key
        )

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
        
        # 약물 등록 폼
        with st.form("drug_form", clear_on_submit=True, enter_to_submit=False):
            drug_name = st.text_input("약물명", placeholder="예: 암로디핀")
            # drug_category는 AI가 자동 분류
            dosage = st.text_input("복용량 (선택)", placeholder="예: 5mg 1일 1회")
            
            submitted = st.form_submit_button("➕ 약물 등록", use_container_width=True)
            
            if submitted and drug_name:
                with st.spinner("약물 분류를 확인 중입니다..."):
                    drug_category = st.session_state.agent.categorize_drug(drug_name)
                
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
    st.markdown("### 🔍 빠른 상호작용 확인")
    st.caption("음식명을 입력하면 등록된 약물과의 상호작용을 바로 확인합니다.")
    
    # 자주 묻는 음식 버튼
    st.markdown("**자주 묻는 음식:**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    food_buttons = [
        ("🍊 자몽", "자몽"),
        ("🍺 맥주", "맥주"),
        ("🥛 우유", "우유"),
        ("☕ 커피", "커피"),
        ("🥬 시금치", "시금치")
    ]
    
    selected_food = None
    for col, (label, food) in zip([col1, col2, col3, col4, col5], food_buttons):
        with col:
            if st.button(label, use_container_width=True):
                selected_food = food
    
    # 직접 입력
    col1, col2 = st.columns([3, 1])
    with col1:
        food_input = st.text_input(
            "음식명 입력",
            placeholder="확인하고 싶은 음식을 입력하세요",
            label_visibility="collapsed"
        )
    with col2:
        check_button = st.button("확인", type="primary", use_container_width=True)
    
    # 확인 실행
    food_to_check = selected_food or (food_input if check_button else None)
    
    if food_to_check:
        result = st.session_state.agent.check_interaction(
            st.session_state.user_id,
            food_to_check
        )
        
        # 결과 표시
        st.markdown("---")
        
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
    # 헤더
    st.markdown('<h1 class="main-header">💊 약궁 (YakGung) 🥗</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">약물-음식 상호작용을 확인하고 안전하게 식사하세요</p>', unsafe_allow_html=True)
    
    # 사이드바
    render_sidebar()
    
    # API 키 확인
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
