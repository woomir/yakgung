# 💊 DrugFood Guard 🥗

**약물-음식 상호작용 확인 AI Agent**

어르신들이 복용하는 약물과 음식 간의 위험한 상호작용을 쉽게 확인할 수 있는 AI 서비스입니다.

## ✨ 주요 기능

1. **약물 등록**: 현재 복용 중인 약물을 등록
2. **빠른 확인**: 특정 음식의 상호작용을 즉시 확인
3. **AI 상담**: 자연어로 질문하고 맞춤 답변 받기
4. **주의 음식 목록**: 피해야 할 음식 한눈에 보기

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python, LangChain
- **Vector DB**: ChromaDB
- **Database**: SQLite
- **LLM**: Google Gemini (Default), OpenAI GPT-4o-mini (Optional)

## 📁 프로젝트 구조

```
drugfood-guard/
├── app/
│   ├── streamlit_app.py   # Streamlit UI
│   ├── config.py          # 설정
│   ├── agent/
│   │   └── agent.py       # AI Agent
│   ├── rag/
│   │   └── vector_store.py # ChromaDB RAG
│   └── db/
│       └── database.py    # SQLite DB
├── data/
│   ├── drug_food_interactions.csv  # 상호작용 데이터
│   ├── drugs.csv                   # 약물 정보
│   ├── foods.csv                   # 음식 정보
│   ├── chroma_db/                  # 벡터 DB
│   └── drugfood.db                 # SQLite DB
├── requirements.txt
├── .env.example
├── run.sh
└── README.md
```

## 🚀 설치 및 실행

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
cp .env.example .env
# .env 파일에서 GOOGLE_API_KEY 설정 (무료)
# 필요시 OPENAI_API_KEY 설정 (유료)
```

### 3. 실행

```bash
# 방법 1: 스크립트 사용
chmod +x run.sh
./run.sh

# 방법 2: 직접 실행
streamlit run app/streamlit_app.py
```

### 4. 접속

브라우저에서 `http://localhost:8501` 접속

## 📊 데이터 현황

| 항목 | 수량 |
|------|------|
| 상호작용 데이터 | 75건 |
| 약물 종류 | 24종 |
| 음식 종류 | 30종 |

### 위험도 분류

- 🔴 **danger**: 절대 금기
- 🟠 **warning**: 가급적 피할 것
- 🟡 **caution**: 주의하여 섭취
- 🟢 **safe**: 안전

## 📖 사용 예시

### 시나리오 1: 혈압약 + 자몽
```
사용자: 암로디핀 먹는데 자몽 먹어도 돼요?
AI: 🔴 위험! 자몽은 암로디핀과 심각한 상호작용이 있습니다.
    자몽의 푸라노쿠마린이 약물 대사를 방해하여 
    혈중 농도가 2-3배 상승할 수 있습니다.
    → 대안: 오렌지, 사과, 배
```

### 시나리오 2: 당뇨약 + 술
```
사용자: 메트포르민 복용 중인데 맥주 마셔도 되나요?
AI: 🔴 위험! 알코올은 메트포르민과 함께 복용 시 
    젖산산증 위험이 있어 생명을 위협할 수 있습니다.
    → 음주를 완전히 피하세요.
```

## ⚠️ 주의사항

- 이 서비스는 참고용 정보를 제공하며, 의학적 조언을 대체하지 않습니다.
- 정확한 정보는 반드시 의사 또는 약사와 상담하세요.

## 📚 데이터 출처

- FDA Drug Interactions Guide
- 식약처 DUR (의약품안전사용서비스)
- DrugBank
- 약학정보원

## 👨‍💻 개발팀

MBA 기말 프로젝트 - DrugFood Guard Team

---

*Health & Wellness RAG Agent AI Project*
