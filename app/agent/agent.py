"""
DrugFood Guard - Agent Module
LangChain을 활용한 AI Agent 구현
"""
from typing import List, Dict, Optional
from pathlib import Path
import sys

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

try:
    from app.config import (
        LLM_PROVIDER,
        OPENAI_API_KEY, OPENAI_MODEL,
        GOOGLE_API_KEY, GEMINI_MODEL,
        SYSTEM_PROMPT, RISK_LEVELS
    )
    from app.rag.vector_store import DrugFoodRAG
    from app.db.database import UserDrugDB
except ImportError:
    # 직접 실행 시
    import os
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    SYSTEM_PROMPT = """당신은 DrugFood Guard의 AI 상담사입니다."""
    RISK_LEVELS = {
        "danger": {"emoji": "🔴", "label": "위험", "color": "#dc3545", "priority": 1},
        "warning": {"emoji": "🟠", "label": "경고", "color": "#fd7e14", "priority": 2},
        "caution": {"emoji": "🟡", "label": "주의", "color": "#ffc107", "priority": 3},
        "safe": {"emoji": "🟢", "label": "안전", "color": "#28a745", "priority": 4},
    }
    # 상대 import
    from rag.vector_store import DrugFoodRAG
    from db.database import UserDrugDB


class DrugFoodAgent:
    """약물-음식 상호작용 AI Agent"""
    
    def __init__(
        self,
        provider: str = LLM_PROVIDER,
        api_key: str = None,
        model: str = None
    ):
        self.provider = provider

        # API 키와 모델 결정
        if provider == "gemini":
            self.api_key = api_key or GOOGLE_API_KEY
            self.model = model or GEMINI_MODEL
        else:  # openai
            self.api_key = api_key or OPENAI_API_KEY
            self.model = model or OPENAI_MODEL

        # LLM 초기화
        self.llm = None
        if self.api_key:
            if provider == "gemini":
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=self.api_key,
                    temperature=0.3
                )
            else:  # openai
                self.llm = ChatOpenAI(
                    api_key=self.api_key,
                    model=self.model,
                    temperature=0.3
                )
        
        # RAG 시스템 초기화
        self.rag = DrugFoodRAG()
        self.rag.build_index()
        
        # 사용자 DB 초기화
        self.user_db = UserDrugDB()
        
        # 대화 기록
        self.conversation_history: List[Dict] = []
    
    def _extract_food_from_query(self, query: str) -> Optional[str]:
        """쿼리에서 음식명 추출 (간단한 규칙 기반)"""
        # 자주 묻는 음식 키워드
        common_foods = [
            "자몽", "자몽주스", "오렌지", "오렌지주스", "사과", "바나나",
            "술", "맥주", "와인", "소주", "알코올",
            "우유", "치즈", "요거트", "유제품",
            "커피", "녹차", "홍차", "카페인",
            "시금치", "브로콜리", "케일", "청국장", "낫토",
            "두유", "두부", "콩",
            "철분제", "칼슘", "비타민"
        ]
        
        query_lower = query.lower()
        for food in common_foods:
            if food in query_lower:
                return food
        
        return None
    
    def _format_interaction_result(self, result: Dict) -> str:
        """검색 결과를 읽기 쉬운 형식으로 포맷"""
        metadata = result.get('metadata', {})
        risk_emoji = result.get('risk_emoji', '❓')
        
        text = f"""
{risk_emoji} **{metadata.get('drug_name', '약물')}** + **{metadata.get('food_name', '음식')}**

- **위험도**: {result.get('risk_label', '알 수 없음')}
- **상호작용**: {metadata.get('interaction_mechanism', '정보 없음')}
- **영향**: {metadata.get('clinical_effect', '정보 없음')}
- **권고사항**: {metadata.get('recommendation', '정보 없음')}
- **대안 음식**: {metadata.get('alternative_food', '없음')}
"""
        return text.strip()
    
    def _build_context(self, user_id: str, query: str) -> str:
        """RAG 검색 및 사용자 컨텍스트 구성"""
        context_parts = []
        
        # 1. 사용자 등록 약물 조회
        user_drugs = self.user_db.get_user_drugs(user_id)
        if user_drugs:
            drug_list = ", ".join([d['drug_name'] for d in user_drugs])
            context_parts.append(f"[사용자 등록 약물]\n{drug_list}")
            
            # 약물 상세 정보
            drug_details = []
            for drug in user_drugs:
                detail = f"- {drug['drug_name']}"
                if drug.get('drug_category'):
                    detail += f" ({drug['drug_category']})"
                if drug.get('dosage'):
                    detail += f" - {drug['dosage']}"
                drug_details.append(detail)
            context_parts.append("\n".join(drug_details))
        
        # 2. RAG 검색
        # 사용자 약물과 쿼리의 음식을 조합하여 검색
        drug_names = [d['drug_name'] for d in user_drugs] if user_drugs else []
        food_name = self._extract_food_from_query(query)
        
        search_results = []
        
        if drug_names and food_name:
            # 특정 약물-음식 조합 검색
            for drug in drug_names:
                result = self.rag.search_by_drug_and_food(drug, food_name)
                if result:
                    search_results.append(result)
        elif drug_names:
            # 등록된 약물의 모든 상호작용 검색
            search_results = self.rag.get_interactions_for_drugs(
                drug_names, 
                risk_levels=["danger", "warning", "caution"]
            )[:10]
        else:
            # 일반 검색
            search_results = self.rag.search(query, n_results=5)
        
        # 검색 결과 포맷팅
        if search_results:
            context_parts.append("\n[관련 약물-음식 상호작용 정보]")
            for result in search_results[:5]:
                context_parts.append(self._format_interaction_result(result))
        
        return "\n\n".join(context_parts)
    
    def chat(
        self, 
        user_id: str, 
        message: str,
        use_history: bool = True
    ) -> Dict:
        """사용자 메시지에 응답"""
        
        # API 키 체크
        if not self.llm:
            provider_name = "Google Gemini" if self.provider == "gemini" else "OpenAI"
            return {
                "success": False,
                "response": f"⚠️ {provider_name} API 키가 설정되지 않았습니다. 설정에서 API 키를 입력해주세요.",
                "context": None,
                "sources": []
            }
        
        # 컨텍스트 구성
        context = self._build_context(user_id, message)
        
        # 시스템 프롬프트 구성
        system_message = f"""{SYSTEM_PROMPT}

## 현재 컨텍스트
{context}
"""
        
        # 메시지 구성
        messages = [SystemMessage(content=system_message)]
        
        # 대화 기록 추가
        if use_history and self.conversation_history:
            for hist in self.conversation_history[-6:]:  # 최근 3턴
                if hist['role'] == 'user':
                    messages.append(HumanMessage(content=hist['content']))
                else:
                    messages.append(AIMessage(content=hist['content']))
        
        messages.append(HumanMessage(content=message))
        
        try:
            # LLM 호출
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # 대화 기록 저장
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_text
            })
            
            # DB에 질문 기록 저장
            self.user_db.save_query(user_id, message, response_text)
            
            return {
                "success": True,
                "response": response_text,
                "context": context,
                "sources": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": f"⚠️ 오류가 발생했습니다: {str(e)}",
                "context": context,
                "sources": []
            }
    
    def check_interaction(
        self, 
        user_id: str, 
        food_name: str
    ) -> Dict:
        """특정 음식에 대한 상호작용 확인 (빠른 조회)"""
        
        user_drugs = self.user_db.get_user_drug_names(user_id)
        
        if not user_drugs:
            return {
                "has_interaction": False,
                "message": "등록된 약물이 없습니다. 먼저 복용 중인 약물을 등록해주세요.",
                "interactions": [],
                "danger_count": 0,
                "warning_count": 0
            }
        
        interactions = []
        for drug_name in user_drugs:
            result = self.rag.search_by_drug_and_food(drug_name, food_name)
            if result:
                # 실제로 해당 음식인지 확인
                result_food = result['metadata'].get('food_name', '').lower()
                if food_name.lower() in result_food or result_food in food_name.lower():
                    interactions.append({
                        "drug_name": drug_name,
                        "food_name": result['metadata'].get('food_name', food_name),
                        "risk_level": result['metadata'].get('risk_level'),
                        "risk_emoji": result['risk_emoji'],
                        "risk_label": result['risk_label'],
                        "recommendation": result['metadata'].get('recommendation'),
                        "alternative": result['metadata'].get('alternative_food')
                    })
        
        # 위험도별 분류
        danger_count = sum(1 for i in interactions if i['risk_level'] == 'danger')
        warning_count = sum(1 for i in interactions if i['risk_level'] == 'warning')
        caution_count = sum(1 for i in interactions if i['risk_level'] == 'caution')
        safe_count = sum(1 for i in interactions if i['risk_level'] == 'safe')
        
        if danger_count > 0:
            message = f"🔴 위험! '{food_name}'은(는) 복용 중인 약물과 심각한 상호작용이 있습니다."
        elif warning_count > 0:
            message = f"🟠 주의! '{food_name}'은(는) 복용 중인 약물과 상호작용 가능성이 있습니다."
        elif caution_count > 0:
            message = f"🟡 '{food_name}'은(는) 주의가 필요하지만 섭취 가능합니다."
        elif safe_count > 0:
            message = f"🟢 '{food_name}'은(는) 등록된 약물과 안전하게 섭취할 수 있습니다."
        elif interactions:
            message = f"🟢 '{food_name}'에 대한 상호작용 정보가 있습니다."
        else:
            message = f"ℹ️ '{food_name}'은(는) 등록된 약물과 알려진 상호작용이 없습니다. (데이터베이스에 정보 없음)"
        
        return {
            "has_interaction": len(interactions) > 0,
            "danger_count": danger_count,
            "warning_count": warning_count,
            "caution_count": caution_count,
            "safe_count": safe_count,
            "message": message,
            "interactions": interactions
        }
    
    def get_all_warnings(self, user_id: str) -> List[Dict]:
        """사용자의 모든 약물에 대한 주의 음식 목록"""
        user_drugs = self.user_db.get_user_drug_names(user_id)
        
        if not user_drugs:
            return []
        
        all_warnings = []
        for drug_name in user_drugs:
            dangerous = self.rag.get_dangerous_foods_for_drug(drug_name)
            for d in dangerous:
                all_warnings.append({
                    "drug_name": drug_name,
                    "food_name": d['metadata'].get('food_name'),
                    "risk_level": d['metadata'].get('risk_level'),
                    "risk_emoji": d['risk_emoji'],
                    "recommendation": d['metadata'].get('recommendation')
                })
        
        return all_warnings
    
    def categorize_drug(self, drug_name: str) -> str:
        """약물명을 기반으로 카테고리 자동 분류"""
        if not self.llm:
            return "기타"
            
        categories = ["혈압약", "당뇨약", "고지혈증약", "항응고제", "항생제", "진통제", "위장약", "갑상선약", "비타민/영양제"]
        
        prompt = f"""
        약물명 '{drug_name}'의 주된 분류는 무엇입니까?
        다음 목록 중에서 가장 적절한 하나만 선택하여 답변하세요. 목록에 없으면 '기타'라고 답변하세요.
        
        목록: {", ".join(categories)}
        
        답변 (단어만):
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            category = response.content.strip()
            
            # 응답이 목록에 있는지 확인
            if category in categories:
                return category
            
            # 목록에 없지만 포함되는 경우 (예: "혈압약입니다" -> "혈압약")
            for cat in categories:
                if cat in category:
                    return cat
                    
            return "기타"
        except Exception as e:
            return f"Error: {str(e)}"

    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []


# 테스트 코드
if __name__ == "__main__":
    print("=== DrugFood Agent 테스트 ===\n")
    
    # Agent 생성 (API 키 없이 테스트)
    agent = DrugFoodAgent(api_key="")
    
    test_user = "test_user_001"
    
    # 약물 등록
    agent.user_db.register_drug(
        user_id=test_user,
        drug_name="암로디핀",
        drug_ingredient="암로디핀베실산염",
        drug_category="혈압약"
    )
    agent.user_db.register_drug(
        user_id=test_user,
        drug_name="메트포르민",
        drug_ingredient="메트포르민염산염",
        drug_category="당뇨약"
    )
    
    print("1. 등록된 약물:")
    drugs = agent.user_db.get_user_drugs(test_user)
    for d in drugs:
        print(f"   - {d['drug_name']}")
    
    # 상호작용 확인
    print("\n2. 자몽 상호작용 확인:")
    result = agent.check_interaction(test_user, "자몽")
    print(f"   {result['message']}")
    for inter in result['interactions']:
        print(f"   {inter['risk_emoji']} {inter['drug_name']}: {inter['recommendation']}")
    
    print("\n3. 맥주 상호작용 확인:")
    result = agent.check_interaction(test_user, "맥주")
    print(f"   {result['message']}")
    
    print("\n4. 사과 상호작용 확인:")
    result = agent.check_interaction(test_user, "사과")
    print(f"   {result['message']}")
    
    # 모든 주의 음식
    print("\n5. 모든 주의 음식:")
    warnings = agent.get_all_warnings(test_user)
    for w in warnings[:5]:
        print(f"   {w['risk_emoji']} {w['drug_name']} + {w['food_name']}")
