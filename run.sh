#!/bin/bash
# DrugFood Guard 실행 스크립트

echo "======================================"
echo "   약식 (DrugFood Guard) 💊🥗"
echo "   약물-음식 상호작용 AI Agent"
echo "======================================"
echo ""

# 현재 디렉토리 설정
cd "$(dirname "$0")"

# 환경변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "✅ 환경변수 로드 완료"
else
    echo "⚠️ .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
fi

# Streamlit 실행
echo ""
echo "🚀 Streamlit 서버 시작..."
echo "   브라우저에서 http://localhost:8501 접속"
echo ""

./venv/bin/streamlit run app/streamlit_app.py --server.port 8501 --server.address localhost
