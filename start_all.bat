@echo off
title Launch Production RAG Chatbot
echo ===============================================================================
echo            STARTING FULL PRODUCTION RAG DOCUMENT CHATBOT SYSTEM
echo ===============================================================================
echo.

echo Cleaning up any old processes on ports 3000, 8000, 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [1/3] Launching FastAPI Core AI Backend (Port 8000)...
start "FastAPI Core AI Backend" cmd /k "%~dp0start_backend.bat"

ping 127.0.0.1 -n 4 >nul

echo [2/3] Launching Node.js API Gateway (Port 3000)...
start "Node.js API Gateway" cmd /k "%~dp0start_gateway.bat"

ping 127.0.0.1 -n 3 >nul

echo [3/3] Launching React Frontend (Port 5173)...
start "React Frontend (Vite)" cmd /k "%~dp0start_frontend.bat"

ping 127.0.0.1 -n 4 >nul

echo.
echo ===============================================================================
echo Opening Web Application UI in your browser...
echo App URL: http://localhost:5173
echo ===============================================================================

start http://localhost:5173
