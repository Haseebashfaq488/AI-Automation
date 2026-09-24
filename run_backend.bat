@echo off
title Jarvis Backend Service (Port 8000)
cd /d "D:\AI-Automation\backend"
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1

:loop
echo ===================================================
echo [%date% %time%] Starting Jarvis FastAPI Backend on port 8000...
echo ===================================================
"C:\Users\BH GMAING\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo ===================================================
echo [WARNING] FastAPI Backend stopped or crashed.
echo Restarting in 30 seconds... (Press Ctrl+C to abort)
echo ===================================================
timeout /t 30 /nobreak
goto loop
