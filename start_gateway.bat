@echo off
title RAG API Gateway (Node.js)
echo Starting Node.js API Gateway on http://localhost:3000 ...
cd /d "%~dp0gateway"
node server.js
pause
