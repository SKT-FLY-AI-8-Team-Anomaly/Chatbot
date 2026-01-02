@echo off
cd /d "%~dp0"
cd backend

if not exist venv (
    echo 가상환경 생성 중...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist venv\Scripts\pip.exe (
    echo 패키지 설치 중...
    pip install -r requirements.txt
)

echo 백엔드 서버 시작...
python main.py

