@echo off
title RAG React Frontend (Vite)
echo Starting React Vite Frontend on http://localhost:5173 ...
cd /d "%~dp0frontend"
call npm.cmd run dev
pause
