# DrugFood Guard 배포 가이드

이 문서는 **Streamlit Community Cloud**를 사용하여 DrugFood Guard 애플리케이션을 무료로 배포하는 방법을 설명합니다.

## 1. 준비 사항

### 1.1 GitHub 저장소 준비
배포를 위해서는 코드가 GitHub에 업로드되어 있어야 합니다.
1. GitHub에 로그인하고 새 Repository를 생성합니다 (Public 권장).
2. 현재 프로젝트 코드를 해당 Repository에 Push합니다.

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <당신의_GITHUB_REPO_URL>
git push -u origin main
```

### 1.2 필수 파일 확인
다음 파일들이 프로젝트 루트에 있는지 확인하세요 (이미 준비되어 있습니다):
- `requirements.txt`: 필요한 라이브러리 목록
- `app/streamlit_app.py`: 메인 애플리케이션 파일

## 2. Streamlit Community Cloud 배포

1. [Streamlit Community Cloud](https://streamlit.io/cloud)에 접속하여 로그인합니다 (GitHub 계정 연동).
2. **"New app"** 버튼을 클릭합니다.
3. **"Use existing repo"**를 선택합니다.
4. 다음 정보를 입력합니다:
    - **Repository**: 방금 생성한 GitHub 저장소 선택
    - **Branch**: `main` (또는 업로드한 브랜치명)
    - **Main file path**: `app/streamlit_app.py`
5. **"Deploy!"** 버튼을 클릭합니다.

## 3. 환경 변수 (Secrets) 설정

앱이 실행되려면 API Key 설정이 필요합니다. 코드를 GitHub에 올릴 때 `.env` 파일은 보안상 제외되므로, Streamlit 대시보드에서 따로 설정해줘야 합니다.

1. 배포 중인 앱 화면 오른쪽 하단의 **"Manage app"** 버튼을 클릭합니다.
2. **"Settings"** 메뉴의 **"Secrets"** 탭으로 이동합니다.
3. 다음 내용을 복사하여 붙여넣고 저장합니다:

```toml
# .env 파일의 내용과 동일하게 입력
LLM_PROVIDER = "gemini"
GOOGLE_API_KEY = "여기에_당신의_GOOGLE_API_KEY를_입력하세요"

# 필요한 경우 추가
# OPENAI_API_KEY = "..." 
```

4. **"Save"**를 누르면 앱이 자동으로 재시작되며 배포가 완료됩니다.

## 4. 배포 완료

이제 제공된 URL (예: `https://drugfood-guard.streamlit.app`)을 통해 누구나 당신의 앱을 사용할 수 있습니다!
