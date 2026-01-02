# SKT FLY AI 챗봇

SKT FLY AI Challenger 프로그램 안내 챗봇 애플리케이션입니다.

## 프로젝트 구조

```
chatbot/
├── frontend/
│   ├── index.html          # 프론트엔드 HTML 파일
│   ├── package.json        # Node.js 설정
│   └── server.py           # Python 서버 (Node.js 없을 때)
├── backend/
│   ├── main.py             # FastAPI 백엔드 애플리케이션
│   └── requirements.txt    # Python 의존성 패키지
├── chatbot-backend.bat     # 백엔드 실행 스크립트
└── chatbot-frontend.bat    # 프론트엔드 실행 스크립트
```

## 설치 및 실행

### 🚀 빠른 시작

프로젝트 루트 디렉토리에서:

```cmd
chatbot-backend.bat    # 백엔드 시작
chatbot-frontend.bat   # 프론트엔드 시작 (index.html 자동으로 열림)
```

### 수동 실행

#### 백엔드

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

#### 프론트엔드

**Node.js 사용:**

```cmd
cd frontend
npm start
```

**Python 사용:**

```cmd
cd frontend
python server.py
```

브라우저에서 `http://localhost:3000` 접속 (자동으로 열림)

## API 엔드포인트

### POST /api/chat

챗봇과 대화하기

**요청:**

```json
{
    "message": "프로그램 소개"
}
```

**응답:**

```json
{
    "response": "SKT FLY AI Challenger는 SK텔레콤의 ESG 사업으로..."
}
```

### GET /api/health

서버 상태 확인

**응답:**

```json
{
    "status": "healthy",
    "service": "SKT FLY AI 챗봇"
}
```

## 개발 환경

**백엔드:**

-   Python 3.8+
-   FastAPI 0.104.1
-   Uvicorn 0.24.0

**프론트엔드:**

-   Node.js (권장) 또는 Python 3.x
-   `http-server` 패키지 (npx로 자동 설치)

## 기능

-   프로그램 소개
-   지원 자격 안내
-   교육 기간 정보
-   커리큘럼 안내
-   혜택 정보
-   자연어 질문 처리
