
@echo off
setlocal
title CLOUD-30 Launcher

set "ROOT=%~dp0"
set "FRONTEND=%ROOT%frontend"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "CONTAINER=cloud30-elasticsearch"

echo ==========================================
echo       CLOUD-30 PROJECT STARTER
echo ==========================================

REM Check Docker and Python
where docker >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker CLI not found.
    goto :fail
)

if not exist "%PYTHON%" (
    echo ERROR: Python executable not found: %PYTHON%
    goto :fail
)

REM 1. FRONTEND
echo.
echo [1/3] Starting Frontend...

powershell -NoProfile -Command "try { Invoke-WebRequest 'http://127.0.0.1:5173/' -TimeoutSec 2 -UseBasicParsing ^| Out-Null; exit 0 } catch { exit 1 }"

if errorlevel 1 (
    start "CLOUD-30 Frontend" cmd /k "cd /d ""%FRONTEND%"" && npm run dev -- --host 127.0.0.1"
) else (
    echo Frontend already running.
)

REM 2. ELASTICSEARCH
echo.
echo [2/3] Starting Elasticsearch...

docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running.
    goto :fail
)

docker inspect "%CONTAINER%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Container "%CONTAINER%" not found.
    goto :fail
)

for /f "delims=" %%S in ('docker inspect --format "{{.State.Running}}" "%CONTAINER%"') do set "ES_RUNNING=%%S"

if /i not "%ES_RUNNING%"=="true" (
    docker start "%CONTAINER%"
    if errorlevel 1 (
        echo ERROR: Could not start Elasticsearch container.
        goto :fail
    )
) else (
    echo Elasticsearch container already running.
)

REM Wait up to 20 seconds for Elasticsearch
powershell -NoProfile -Command "$d=(Get-Date).AddSeconds(20); do { try { $r=Invoke-RestMethod 'http://localhost:9200/_cluster/health' -TimeoutSec 2; if ($r.status -in @('green','yellow')) { exit 0 } } catch {}; Start-Sleep 1 } while ((Get-Date) -lt $d); exit 1"

if errorlevel 1 (
    echo WARNING: Elasticsearch has not responded yet.
    echo Check Docker Desktop and the container logs.
) else (
    echo Elasticsearch is ready.
)




REM 3. BACKEND
echo.
echo [3/3] Starting FastAPI Backend...

if not exist "%ROOT%api\main.py" (
    echo ERROR: api\main.py not found.
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo ERROR: Python executable not found:
    echo %PYTHON%
    pause
    exit /b 1
)

REM Check whether the backend is already responding
powershell -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2 ^| Out-Null; exit 0 } catch { exit 1 }"

if not errorlevel 1 (
    echo Backend is already running.
) else (
    echo Opening backend terminal...
    start "CLOUD-30 Backend" /D "%ROOT%" "%PYTHON%" -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
)

echo Backend launch command sent.

echo.
echo Startup commands completed.
echo Frontend:      http://127.0.0.1:5173/
echo Elasticsearch: http://localhost:9200
echo Backend:       http://127.0.0.1:8000/health
echo API docs:      http://127.0.0.1:8000/docs
echo.
start "" "http://127.0.0.1:5173/"
pause
exit /b 0

:fail
echo.
echo Startup failed. Read the error above.
pause
exit /b 1
