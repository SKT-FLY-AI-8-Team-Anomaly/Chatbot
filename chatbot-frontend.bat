@echo off
cd /d "%~dp0\frontend"

echo 프론트엔드 서버 시작 중...

where node >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    if exist package.json (
        npm start
    ) else (
        npx http-server . -p 3000 -o -c-1 -d false
    )
) else (
    if exist server.py (
        python server.py
    ) else (
        start http://localhost:3000/index.html
        python -m http.server 3000
    )
)
