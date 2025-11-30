# DrugFood Guard - AI Agent 프로젝트 기획서

> **문서 목적**: AI 시스템이 프로젝트 맥락을 이해하고 개발을 지원할 수 있도록 구조화된 기획 정보 제공
> **버전**: 1.1 (Updated)
> **최종 수정**: 2024-11-30

---

## 1. 프로젝트 메타데이터

```yaml
project_name: DrugFood Guard
project_type: RAG-based AI Agent
domain: Healthcare / Medication Safety
target_users: 다약제 복용 고령자, 보호자, 일반 사용자
language: Korean (primary), English (secondary)
development_period: 6 weeks
team_size: 4 members
current_status: MVP Implemented
```

---

## 2. 프로젝트 정의

### 2.1 한 줄 요약
복용 중인 약물과 음식/음료/건강기능식품 간의 상호작용 위험을 실시간으로 분석하여 안전한 복약 생활을 지원하는 RAG 기반 AI Agent

### 2.2 핵심 가치 제안 (Value Proposition)
- **문제 (Problem)**: 다약제 복용자가 증가하는 고령화 사회에서 약-음식 상호작용 정보 접근성이 낮아 부작용 위험에 노출됨
- **해결책 (Solution)**: AI Agent가 개인 복용 약물 기반으로 음식 섭취 가능 여부를 즉시 판단하고 안전한 대안 제시
- **차별점 (Differentiation)**: 기존 앱은 약-약 상호작용만 제공, 본 서비스는 약-음식 상호작용에 특화

---

## 3. 구현된 기능 (Implemented Features)

### 3.1 사용자 경험 (UX)
- **Landing Page (첫 화면)**:
    - 프리미엄 다크 테마 디자인 (Glassmorphism, Gradients)
    - 서비스 소개 (Hero Section), 문제 정의, 핵심 기능, 기대 효과 섹션
    - **시작하기** 버튼을 통한 서비스 진입
- **인증 (Authentication)**:
    - `streamlit-authenticator` 기반 로그인/회원가입
    - 비밀번호 해싱 (bcrypt) 및 보안 처리
    - 면책 조항 동의 (Registration 단계)
    - **로그아웃 시 첫 화면으로 리다이렉트**

### 3.2 핵심 기능
- **내 약물 관리 (My Drugs)**:
    - `drugs.csv` 기반 약물명 자동완성 검색 및 등록
    - 사용자별 등록 약물 영구 저장 (SQLite)
- **빠른 확인 (Quick Check)**:
    - 음식 카테고리별(과일, 채소, 육류 등) 빠른 선택 버튼
    - 특정 음식 입력 시 즉시 상호작용 분석 결과 제공
- **AI 약사 상담 (AI Chat)**:
    - RAG 기반 자연어 질의응답 ("자몽 먹어도 돼?")
    - 등록된 약물 컨텍스트 자동 반영
    - 위험도, 이유, 권고사항, 대안 음식 제시
- **주의 음식 목록 (Warnings)**:
    - 등록된 약물에 대해 피해야 할 음식 목록 자동 생성 및 시각화
- **약물 DB 뷰어 (Drug DB Viewer)**:
    - 전체 의약품 목록 (`drugs.csv`) 조회 및 검색
    - 약물-음식 상호작용 규칙 (`drug_food_interactions.csv`) 필터링 및 조회

---

## 4. 시스템 아키텍처

### 4.1 기술 스택
```yaml
frontend:
  framework: Streamlit
  libraries: streamlit-authenticator, pandas
  design: Custom CSS (Dark Theme)

backend:
  language: Python 3.9+
  framework: LangChain
  database: SQLite (User Data)

llm:
  provider: Google Gemini
  model: gemini-1.5-flash
  reason: 속도, 비용 효율, 긴 컨텍스트 처리

vector_database:
  engine: ChromaDB
  embedding: Google Generative AI Embeddings
  reason: 로컬 실행 가능, 고성능

deployment:
  platform: Streamlit Community Cloud
  secrets: st.secrets (API Keys)
```

### 4.2 데이터 모델
```sql
-- 사용자 테이블
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 사용자 약물 테이블
CREATE TABLE user_drugs (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    drug_name TEXT,
    drug_ingredient TEXT,
    drug_category TEXT,
    dosage TEXT,
    registered_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, drug_name)
);
```

---

## 5. 데이터 소스

### 5.1 보유 데이터
- **의약품 데이터 (`drugs.csv`)**: 주요 만성질환 약물 정보 (성분, 효능, 주의사항)
- **상호작용 데이터 (`drug_food_interactions.csv`)**: 약물-음식 간 상호작용 규칙, 위험도, 메커니즘, 대안 음식

### 5.2 위험도 분류
- 🔴 **Danger (위험)**: 절대 금기 (예: 와파린+청국장)
- 🟠 **Warning (경고)**: 가급적 피할 것
- 🟡 **Caution (주의)**: 시간 간격 두고 섭취
- 🟢 **Safe (안전)**: 상호작용 없음

---

## 6. 파일 구조

```
drugfood-guard/
├── app/
│   ├── __init__.py
│   ├── config.py              # 환경 설정
│   ├── streamlit_app.py       # 메인 UI (Landing, Auth, Tabs)
│   ├── agent/
│   │   └── agent.py           # AI Agent & RAG Logic
│   ├── rag/
│   │   └── vector_store.py    # ChromaDB Management
│   └── db/
│       └── database.py        # SQLite User DB
├── data/
│   ├── drug_food_interactions.csv
│   ├── drugs.csv
│   └── foods.csv
├── auth_config.yaml           # 인증 설정 (Credentials)
├── requirements.txt
├── README.md
└── PROJECT_SPEC.md            # 이 문서
```

---

## 7. 실행 방법

### 7.1 로컬 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# Streamlit 실행
streamlit run app/streamlit_app.py
```

### 7.2 환경 변수 설정 (.env)
```
GOOGLE_API_KEY=your_api_key_here
```

---

**문서 끝**
