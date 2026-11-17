@echo off
title RAG Core AI Backend (FastAPI)
echo Starting FastAPI Core AI Backend on http://127.0.0.1:8000 ...
cd /d "%~dp0backend"

set VENV_PY="%~dp0backend\.venv\Scripts\python.exe"
if exist %VENV_PY% (
    %VENV_PY% -m uvicorn app.main:app --host 127.0.0.1 --port 8000
) else if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
)
pause
