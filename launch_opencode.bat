@echo off
title OpenCode Interactive CLI - Jarvis AI
cls
echo ===============================================================================
echo   Jarvis AI - OpenCode Interactive Terminal
echo   Directory: %~dp0
echo ===============================================================================
echo.

cd /d "%~dp0"

set "OPENCODE_EXE=C:\Users\BH GMAING\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe"

if exist "%OPENCODE_EXE%" (
    echo Starting OpenCode CLI...
    echo.
    "%OPENCODE_EXE%" %*
) else (
    where opencode.cmd >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        call opencode.cmd %*
    ) else (
        echo [ERROR] OpenCode binary not found at %OPENCODE_EXE%
        pause
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [EXIT] OpenCode exited with code %ERRORLEVEL%.
    pause
)
