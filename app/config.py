"""
DrugFood Guard - Configuration Module
환경 설정 및 상수 관리
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Streamlit Secrets 로드 시도
try:
    import streamlit as st
    secrets = st.secrets
except (ImportError, FileNotFoundError):
    secrets = {}

# LLM 설정 (OpenAI or Google Gemini)
LLM_PROVIDER = secrets.get("LLM_PROVIDER", os.getenv("LLM_PROVIDER", "gemini"))

# OpenAI 설정
OPENAI_API_KEY = secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
OPENAI_MODEL = secrets.get("OPENAI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

# Google Gemini 설정
GOOGLE_API_KEY = secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GEMINI_MODEL = secrets.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

# ChromaDB 설정
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")
COLLECTION_NAME = "drug_food_interactions"

# SQLite 설정
SQLITE_DB_PATH = str(DATA_DIR / "drugfood.db")

# 데이터 파일 경로
INTERACTIONS_CSV = str(DATA_DIR / "drug_food_interactions.csv")
DRUGS_CSV = str(DATA_DIR / "drugs.csv")
FOODS_CSV = str(DATA_DIR / "foods.csv")

# 위험도 레벨 정의
RISK_LEVELS = {
    "danger": {"emoji": "🔴", "label": "위험", "color": "#dc3545", "priority": 1},
    "warning": {"emoji": "🟠", "label": "경고", "color": "#fd7e14", "priority": 2},
    "caution": {"emoji": "🟡", "label": "주의", "color": "#ffc107", "priority": 3},
    "safe": {"emoji": "🟢", "label": "안전", "color": "#28a745", "priority": 4},
}

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 DrugFood Guard의 AI 상담사입니다. 
사용자가 복용 중인 약물과 음식 간의 상호작용을 분석하고 안전한 식이 정보를 제공합니다.

## 역할
1. 사용자가 등록한 약물 정보를 기억하고 활용합니다.
2. 약물-음식 상호작용 데이터베이스를 검색하여 정확한 정보를 제공합니다.
3. 위험한 조합은 명확하게 경고하고, 안전한 대안을 제시합니다.
4. 어르신도 이해하기 쉬운 친절한 한국어로 설명합니다.

## 응답 형식
- 위험도를 이모지로 표시: 🔴위험, 🟠경고, 🟡주의, 🟢안전
- 핵심 정보를 먼저 제공하고, 상세 설명은 뒤에 추가
- 대안 음식이 있으면 반드시 제안
- 의학적 조언은 반드시 의사/약사 상담 권고

## 주의사항
- 데이터베이스에 없는 정보는 "확인되지 않음"으로 표시
- 추측이나 불확실한 정보는 제공하지 않음
- 응급 상황으로 판단되면 즉시 119 또는 병원 방문 권고
"""

# RAG 설정
RAG_TOP_K = 5  # 검색 결과 수
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
