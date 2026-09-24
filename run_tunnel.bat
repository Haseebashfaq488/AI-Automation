@echo off
title Jarvis ngrok Tunnel Service
cd /d "D:\AI-Automation"

:loop
echo ===================================================
echo [%date% %time%] Starting Jarvis ngrok Tunnel Service...
echo ===================================================
"C:\Users\BH GMAING\AppData\Local\Programs\Python\Python313\python.exe" -u "D:\AI-Automation\run_tunnel.py"
echo.
echo ===================================================
echo [WARNING] Tunnel process exited.
echo Restarting in 30 seconds... (Press Ctrl+C to abort)
echo ===================================================
timeout /t 30 /nobreak
goto loop
