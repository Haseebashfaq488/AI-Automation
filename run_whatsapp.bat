@echo off
title Jarvis WhatsApp Service (Port 4097)
cd /d "D:\AI-Automation\backend\whatsapp_service"

:loop
echo ===================================================
echo [%date% %time%] Starting Jarvis WhatsApp DOM Sidecar on port 4097...
echo ===================================================
node server.js
echo.
echo ===================================================
echo [WARNING] WhatsApp Service stopped or crashed.
echo Restarting in 30 seconds... (Press Ctrl+C to abort)
echo ===================================================
timeout /t 30 /nobreak
goto loop
