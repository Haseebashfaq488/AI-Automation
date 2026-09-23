@echo off
title Google Antigravity CLI (agy) - Jarvis AI
cls
echo ===============================================================================
echo   Jarvis AI - Google Antigravity CLI (agy) Interactive Setup
echo   Directory: %~dp0
echo ===============================================================================
echo.

set "AGY_EXE=%LOCALAPPDATA%\agy\bin\agy.exe"

echo Starting Antigravity CLI in PowerShell...
echo If this is your first time, it will prompt for login.
echo.
powershell.exe -NoExit -Command "& '%AGY_EXE%'"
pause
