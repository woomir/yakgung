"""
DrugFood Guard - RAG Module
ChromaDB를 활용한 약물-음식 상호작용 데이터 벡터 저장 및 검색
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
import sys

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.config import (
        CHROMA_PERSIST_DIR, 
        COLLECTION_NAME,
        INTERACTIONS_CSV,
        DRUGS_CSV,
        FOODS_CSV,
        RAG_TOP_K,
        RISK_LEVELS
    )
except ImportError:
    # 직접 실행 시 기본값 설정
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")
    COLLECTION_NAME = "drug_food_interactions"
    INTERACTIONS_CSV = str(DATA_DIR / "drug_food_interactions.csv")
    DRUGS_CSV = str(DATA_DIR / "drugs.csv")
    FOODS_CSV = str(DATA_DIR / "foods.csv")
    RAG_TOP_K = 5
    RISK_LEVELS = {
        "danger": {"emoji": "🔴", "label": "위험", "color": "#dc3545", "priority": 1},
        "warning": {"emoji": "🟠", "label": "경고", "color": "#fd7e14", "priority": 2},
        "caution": {"emoji": "🟡", "label": "주의", "color": "#ffc107", "priority": 3},
        "safe": {"emoji": "🟢", "label": "안전", "color": "#28a745", "priority": 4},
    }


class DrugFoodRAG:
    """약물-음식 상호작용 RAG 시스템"""
    
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Gemini API Quota 제한으로 인해 로컬 임베딩(ONNX MiniLM)으로 전환
        # ChromaDB 기본 임베딩 사용 (무료, 무제한, 로컬 동작)
        self.embedding_fn = None 
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 컬렉션 가져오기 또는 생성
        try:
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Drug-Food Interactions Database"}
                # embedding_function=None implies default
            )
        except ValueError as e:
            # 임베딩 함수 변경으로 인한 충돌 시 컬렉션 재성성
            if "Embedding function conflict" in str(e):
                print("⚠️ 임베딩 함수 변경 감지. 컬렉션을 재생성합니다.")
                self.client.delete_collection(COLLECTION_NAME)
                self.collection = self.client.create_collection(
                    name=COLLECTION_NAME,
                    metadata={"description": "Drug-Food Interactions Database"}
                )
            else:
                raise e
        
        # 약물 및 음식 데이터 로드
        self.drugs_df = None
        self.foods_df = None
        self.interactions_df = None
        self._load_data()
    
    def _load_data(self):
        """CSV 데이터 로드"""
        try:
            if Path(INTERACTIONS_CSV).exists():
                self.interactions_df = pd.read_csv(INTERACTIONS_CSV)
            if Path(DRUGS_CSV).exists():
                self.drugs_df = pd.read_csv(DRUGS_CSV)
            if Path(FOODS_CSV).exists():
                self.foods_df = pd.read_csv(FOODS_CSV)
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
    
    def _create_document(self, row: pd.Series) -> str:
        """상호작용 데이터를 검색 가능한 문서로 변환"""
        doc = f"""약물명: {row['drug_name']}
성분명: {row['drug_ingredient']}
약물분류: {row['drug_category']}
음식명: {row['food_name']}
음식분류: {row['food_category']}
위험도: {row['risk_level']}
상호작용 메커니즘: {row['interaction_mechanism']}
임상적 영향: {row['clinical_effect']}
권고사항: {row['recommendation']}
대안 음식: {row['alternative_food']}
출처: {row['source']}"""
        return doc
    
    def _create_metadata(self, row: pd.Series) -> Dict:
        """메타데이터 생성"""
        risk_info = RISK_LEVELS.get(row['risk_level'], RISK_LEVELS['caution'])
        return {
            "drug_name": str(row['drug_name']),
            "drug_ingredient": str(row['drug_ingredient']),
            "drug_category": str(row['drug_category']),
            "food_name": str(row['food_name']),
            "food_category": str(row['food_category']),
            "risk_level": str(row['risk_level']),
            "risk_priority": risk_info['priority'],
            "recommendation": str(row['recommendation']),
            "alternative_food": str(row['alternative_food']),
            "source": str(row['source'])
        }
    
    def build_index(self, force_rebuild: bool = False) -> Dict:
        """벡터 인덱스 구축"""
        if self.interactions_df is None:
            return {"success": False, "message": "상호작용 데이터가 없습니다."}
        
        # 기존 데이터 확인
        existing_count = self.collection.count()
        if existing_count > 0 and not force_rebuild:
            return {
                "success": True, 
                "message": f"기존 인덱스 사용 ({existing_count}개 문서)",
                "count": existing_count
            }
        
        # 강제 재구축 시 기존 데이터 삭제
        if force_rebuild and existing_count > 0:
            # 컬렉션 삭제 후 재생성
            self.client.delete_collection(COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Drug-Food Interactions Database"}
            )
        
        # 문서 생성 및 추가
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in self.interactions_df.iterrows():
            doc = self._create_document(row)
            metadata = self._create_metadata(row)
            doc_id = f"interaction_{idx}"
            
            documents.append(doc)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        # ChromaDB에 추가
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "success": True,
            "message": f"인덱스 구축 완료 ({len(documents)}개 문서)",
            "count": len(documents)
        }
    
    def search(
        self, 
        query: str, 
        n_results: int = RAG_TOP_K,
        drug_filter: Optional[List[str]] = None,
        food_filter: Optional[str] = None,
        risk_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """상호작용 검색 - 키워드 매칭 + 벡터 검색 하이브리드"""
        
        # 1단계: DataFrame에서 직접 키워드 매칭 (더 정확)
        keyword_results = []
        if self.interactions_df is not None:
            df = self.interactions_df.copy()
            
            # 약물 필터
            if drug_filter and len(drug_filter) > 0:
                df = df[df['drug_name'].isin(drug_filter)]
            
            # 음식 필터
            if food_filter:
                df = df[df['food_name'].str.contains(food_filter, case=False, na=False)]
            
            # 위험도 필터
            if risk_filter and len(risk_filter) > 0:
                df = df[df['risk_level'].isin(risk_filter)]
            
            # 쿼리 키워드 매칭
            query_lower = query.lower()
            query_terms = query_lower.split()
            
            for idx, row in df.iterrows():
                score = 0
                drug_name_lower = str(row['drug_name']).lower()
                food_name_lower = str(row['food_name']).lower()
                
                # 약물명 매칭
                for term in query_terms:
                    if term in drug_name_lower:
                        score += 10
                    if term in food_name_lower:
                        score += 10
                
                if score > 0:
                    risk_info = RISK_LEVELS.get(row['risk_level'], RISK_LEVELS['caution'])
                    keyword_results.append({
                        "document": self._create_document(row),
                        "metadata": self._create_metadata(row),
                        "distance": 1 - (score / 20),  # 스코어를 거리로 변환
                        "relevance_score": score / 20,
                        "risk_emoji": risk_info['emoji'],
                        "risk_label": risk_info['label'],
                        "risk_color": risk_info['color']
                    })
        
        # 2단계: 키워드 결과가 충분하면 반환
        if len(keyword_results) >= n_results:
            # 위험도 우선, 그 다음 관련성 순 정렬
            keyword_results.sort(
                key=lambda x: (
                    x['metadata'].get('risk_priority', 99),
                    -x['relevance_score']
                )
            )
            return keyword_results[:n_results]
        
        # 3단계: 벡터 검색 보완 (키워드 결과가 부족한 경우)
        # 필터 조건 구성
        where_conditions = []
        
        if drug_filter and len(drug_filter) > 0:
            if len(drug_filter) == 1:
                where_conditions.append({"drug_name": drug_filter[0]})
            else:
                where_conditions.append({"drug_name": {"$in": drug_filter}})
        
        if food_filter:
            where_conditions.append({"food_name": food_filter})
        
        if risk_filter and len(risk_filter) > 0:
            if len(risk_filter) == 1:
                where_conditions.append({"risk_level": risk_filter[0]})
            else:
                where_conditions.append({"risk_level": {"$in": risk_filter}})
        
        # where 조건 합치기
        where = None
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}
        
        # 검색 실행
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # 더 많이 가져와서 필터링
                where=where,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"검색 오류: {e}")
            # 필터 없이 재시도
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,
                include=["documents", "metadatas", "distances"]
            )
        
        # 결과 포맷팅
        vector_results = []
        if results and results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                risk_info = RISK_LEVELS.get(
                    metadata.get('risk_level', 'caution'), 
                    RISK_LEVELS['caution']
                )
                
                vector_results.append({
                    "document": doc,
                    "metadata": metadata,
                    "distance": distance,
                    "relevance_score": 1 - distance if distance < 1 else 0,
                    "risk_emoji": risk_info['emoji'],
                    "risk_label": risk_info['label'],
                    "risk_color": risk_info['color']
                })
        
        # 키워드 결과와 벡터 결과 합치기 (중복 제거)
        seen = set()
        combined_results = []
        
        for result in keyword_results + vector_results:
            key = (
                result['metadata'].get('drug_name'),
                result['metadata'].get('food_name')
            )
            if key not in seen:
                seen.add(key)
                combined_results.append(result)
        
        # 위험도 우선순위로 정렬
        combined_results.sort(
            key=lambda x: (
                x['metadata'].get('risk_priority', 99),
                x['distance']
            )
        )
        
        return combined_results[:n_results]
    
    def search_by_drug_and_food(
        self, 
        drug_name: str, 
        food_name: str
    ) -> Optional[Dict]:
        """특정 약물-음식 조합 검색"""
        results = self.search(
            query=f"{drug_name} {food_name}",
            n_results=5,
            drug_filter=[drug_name]
        )
        
        # 정확한 음식명 매칭
        for result in results:
            if result['metadata'].get('food_name', '').lower() == food_name.lower():
                return result
        
        # 부분 매칭
        for result in results:
            if food_name.lower() in result['metadata'].get('food_name', '').lower():
                return result
        
        return results[0] if results else None
    
    def get_interactions_for_drugs(
        self, 
        drug_names: List[str],
        risk_levels: Optional[List[str]] = None
    ) -> List[Dict]:
        """여러 약물에 대한 상호작용 조회"""
        all_results = []
        
        for drug_name in drug_names:
            results = self.search(
                query=drug_name,
                n_results=20,
                drug_filter=[drug_name],
                risk_filter=risk_levels
            )
            all_results.extend(results)
        
        # 중복 제거 및 정렬
        seen = set()
        unique_results = []
        for result in all_results:
            key = (
                result['metadata'].get('drug_name'),
                result['metadata'].get('food_name')
            )
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # 위험도 순 정렬
        unique_results.sort(
            key=lambda x: x['metadata'].get('risk_priority', 99)
        )
        
        return unique_results
    
    def get_dangerous_foods_for_drug(self, drug_name: str) -> List[Dict]:
        """특정 약물의 위험 음식 목록"""
        return self.search(
            query=f"{drug_name} 위험 금기",
            n_results=10,
            drug_filter=[drug_name],
            risk_filter=["danger", "warning"]
        )
    
    def get_safe_foods_for_drug(self, drug_name: str) -> List[Dict]:
        """특정 약물의 안전 음식 목록"""
        return self.search(
            query=f"{drug_name} 안전",
            n_results=10,
            drug_filter=[drug_name],
            risk_filter=["safe"]
        )
    
    def get_stats(self) -> Dict:
        """데이터베이스 통계"""
        total = self.collection.count()
        
        stats = {
            "total_interactions": total,
            "drugs": 0,
            "foods": 0,
            "by_risk_level": {}
        }
        
        if self.interactions_df is not None:
            stats["drugs"] = self.interactions_df['drug_name'].nunique()
            stats["foods"] = self.interactions_df['food_name'].nunique()
            stats["by_risk_level"] = self.interactions_df['risk_level'].value_counts().to_dict()
        
        return stats


# 테스트 코드
if __name__ == "__main__":
    print("=== DrugFood RAG 테스트 ===\n")
    
    rag = DrugFoodRAG()
    
    # 인덱스 구축
    print("1. 인덱스 구축")
    result = rag.build_index(force_rebuild=True)
    print(f"   결과: {result}\n")
    
    # 통계 조회
    print("2. 데이터베이스 통계")
    stats = rag.get_stats()
    print(f"   총 상호작용: {stats['total_interactions']}개")
    print(f"   약물 종류: {stats['drugs']}개")
    print(f"   음식 종류: {stats['foods']}개")
    print(f"   위험도별: {stats['by_risk_level']}\n")
    
    # 검색 테스트
    print("3. 검색 테스트: '암로디핀 자몽'")
    results = rag.search("암로디핀 자몽", n_results=3)
    for r in results:
        print(f"   {r['risk_emoji']} {r['metadata']['drug_name']} + {r['metadata']['food_name']}")
        print(f"      → {r['metadata']['recommendation']}\n")
    
    # 특정 약물의 위험 음식
    print("4. 암로디핀의 위험 음식")
    dangerous = rag.get_dangerous_foods_for_drug("암로디핀")
    for d in dangerous[:3]:
        print(f"   {d['risk_emoji']} {d['metadata']['food_name']}: {d['metadata']['recommendation']}")
