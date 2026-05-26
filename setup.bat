@echo off
setlocal EnableDelayedExpansion
title UrivDocs - Setup and Run

:: ╔══════════════════════════════════════════════════════════════════╗
:: ║              UrivDocs - Windows Setup Script                    ║
:: ╚══════════════════════════════════════════════════════════════════╝

color 0B
echo.
echo  ██╗   ██╗██████╗ ██╗██╗   ██╗██████╗  ██████╗  ██████╗███████╗
echo  ██║   ██║██╔══██╗██║██║   ██║██╔══██╗██╔═══██╗██╔════╝██╔════╝
echo  ██║   ██║██████╔╝██║██║   ██║██║  ██║██║   ██║██║     ███████╗
echo  ██║   ██║██╔══██╗██║╚██╗ ██╔╝██║  ██║██║   ██║██║     ╚════██║
echo  ╚██████╔╝██║  ██║██║ ╚████╔╝ ██████╔╝╚██████╔╝╚██████╗███████║
echo   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═════╝  ╚═════╝  ╚═════╝╚══════╝
echo.
echo                 Local AI - Document Intelligence
echo.
color 07

set "SCRIPT_DIR=%~dp0"
set "LLM_MODEL=%~1"
if "%LLM_MODEL%"=="" set "LLM_MODEL=llama3"

cd /d "%SCRIPT_DIR%"

:: ── Check for Docker ─────────────────────────────────────────────
echo [UrivDocs] Checking for Docker...
docker info >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [✓] Docker found - using Docker mode
    goto :DOCKER_MODE
) else (
    echo [!] Docker not running - using local mode
    goto :LOCAL_MODE
)

:: ════════════════════════════════════════════════════════════════════
:DOCKER_MODE
:: ════════════════════════════════════════════════════════════════════
echo.
echo ── Docker Mode ─────────────────────────────────────────────────
echo.

if not exist ".env" (
    copy .env.example .env >nul
    echo [✓] Created .env from .env.example
)

if not exist "storage\uploads"  mkdir storage\uploads
if not exist "storage\vectordb" mkdir storage\vectordb
if not exist "storage\models"   mkdir storage\models

echo [UrivDocs] Stopping existing containers...
docker compose down --remove-orphans >nul 2>&1

echo [UrivDocs] Building Docker images (first run takes a few minutes)...
docker compose build
if %ERRORLEVEL% NEQ 0 ( echo [✗] Docker build failed & pause & exit /b 1 )

echo [UrivDocs] Starting services...
docker compose up -d
if %ERRORLEVEL% NEQ 0 ( echo [✗] Docker start failed & pause & exit /b 1 )

echo [UrivDocs] Waiting for API to start...
:WAIT_API_DOCKER
timeout /t 3 /nobreak >nul
curl -sf http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :WAIT_API_DOCKER
echo [✓] API is ready!

echo [UrivDocs] Pulling LLM model: %LLM_MODEL% (may take a while)...
docker exec urivdocs-ollama ollama pull %LLM_MODEL%

goto :DONE_DOCKER

:: ════════════════════════════════════════════════════════════════════
:LOCAL_MODE
:: ════════════════════════════════════════════════════════════════════
echo.
echo ── Local Mode ──────────────────────────────────────────────────
echo.

:: Check Python
echo [UrivDocs] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found. Please install Python 3.11 from https://python.org
    echo     Make sure to check "Add Python to PATH" during installation
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [✓] %%i

:: Check Node.js
echo [UrivDocs] Checking Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Node.js not found. Please install Node.js from https://nodejs.org
    pause
    start https://nodejs.org/en/download
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo [✓] Node.js %%i

:: Check Ollama
echo [UrivDocs] Checking Ollama...
ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Ollama not found. Downloading installer...
    echo     Please install Ollama and re-run this script.
    start https://ollama.com/download/windows
    pause
    exit /b 1
)
echo [✓] Ollama found

:: Create .env
if not exist ".env" (
    copy .env.example .env >nul
    echo [✓] Created .env from .env.example
)

:: Storage dirs
if not exist "storage\uploads"  mkdir storage\uploads
if not exist "storage\vectordb" mkdir storage\vectordb
if not exist "storage\models"   mkdir storage\models
echo [✓] Storage directories ready

:: Python venv
echo [UrivDocs] Setting up Python environment...
if not exist ".venv" (
    python -m venv .venv
    echo [✓] Virtual environment created
)

echo [UrivDocs] Installing Python dependencies (first run takes a few minutes)...
.venv\Scripts\pip install --upgrade pip -q
.venv\Scripts\pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 ( echo [✗] pip install failed & pause & exit /b 1 )
echo [✓] Python dependencies installed

:: Frontend deps
echo [UrivDocs] Installing frontend dependencies...
cd ui
if not exist "node_modules" (
    npm install
    if %ERRORLEVEL% NEQ 0 ( echo [✗] npm install failed & cd .. & pause & exit /b 1 )
)
cd ..
echo [✓] Frontend dependencies installed

:: Pull Ollama model
echo [UrivDocs] Starting Ollama...
start /B ollama serve
timeout /t 4 /nobreak >nul

echo [UrivDocs] Pulling model: %LLM_MODEL% (may take a while on first run)...
ollama pull %LLM_MODEL%

:: Start API in new window
echo [UrivDocs] Starting FastAPI backend...
start "UrivDocs API" cmd /k "set PYTHONPATH=%SCRIPT_DIR% && .venv\Scripts\uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for API
echo [UrivDocs] Waiting for API...
:WAIT_API_LOCAL
timeout /t 3 /nobreak >nul
curl -sf http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :WAIT_API_LOCAL
echo [✓] API running on http://localhost:8000

:: Start UI in new window
echo [UrivDocs] Starting React frontend...
start "UrivDocs UI" cmd /k "cd ui && npm run dev -- --port 5173"
timeout /t 4 /nobreak >nul

:: Open browser
start http://localhost:5173

echo.
echo ╔══════════════════════════════════════════╗
echo ║      ◈  UrivDocs is Running!  ◈          ║
echo ╚══════════════════════════════════════════╝
echo.
echo   App      -^>  http://localhost:5173
echo   API      -^>  http://localhost:8000
echo   API Docs -^>  http://localhost:8000/docs
echo.
echo   Two terminal windows have opened:
echo     - "UrivDocs API"  = backend server
echo     - "UrivDocs UI"   = frontend dev server
echo.
echo   Close those windows to stop the app.
echo.
pause
exit /b 0

:DONE_DOCKER
echo.
echo ╔══════════════════════════════════════════╗
echo ║      ◈  UrivDocs is Running!  ◈          ║
echo ╚══════════════════════════════════════════╝
echo.
echo   App      -^>  http://localhost:3000
echo   API      -^>  http://localhost:8000
echo   API Docs -^>  http://localhost:8000/docs
echo.
start http://localhost:3000
pause
exit /b 0
