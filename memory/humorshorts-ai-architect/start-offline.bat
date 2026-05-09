@echo off
TITLE Gamma 4 - HumorShorts AI Architect (OFFLINE MODE)
SETLOCAL

echo ======================================================
echo   🚀 Gamma 4 AI Architect - 중국 협업자용 로컬 실행기
echo ======================================================
echo.

:: 1. 의존성 체크
if not exist "node_modules\" (
    echo [!] node_modules가 없습니다. 의존성을 먼저 설치합니다...
    call npm install
)

:: 2. LM Studio 상태 확인 안내
echo [+] 로컬 LM Studio 상태를 확인 중입니다... (127.0.0.1:1234)
netstat -ano | findstr 127.0.0.1:1234 > nul
if %errorlevel% equ 0 (
    echo [OK] LM Studio가 구동 중입니다.
) else (
    echo [!] 경고: LM Studio가 실행 중이지 않은 것 같습니다.
    echo     LM Studio를 먼저 실행해야 AI 기능을 사용할 수 있습니다!
)

echo.
echo [+] 대시보드 서버를 시작합니다... (http://localhost:3000)
echo.

:: 3. Vite 서버 실행 및 브라우저 오픈
start http://localhost:3000
npm run dev

pause
