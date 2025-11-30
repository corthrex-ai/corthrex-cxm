@echo off
cls
echo.
echo ========================================
echo    STARTING CORTHREX CXM - FULL SYSTEM
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Ollama server in background...
start "Corthrex - Ollama" ollama serve

:: Give Ollama 4 seconds to wake up
timeout /t 4 >nul

echo.
if not exist corthrex.cxm (
    echo First-time setup: injecting your identity...
    python genesis_update.py
) else (
    for %%A in (corthrex.cxm) do if %%~zA==0 (
        echo Empty memory file found - injecting identity...
        python genesis_update.py
    ) else (
        echo Memory file already exists - good to go
    )
)

echo.
echo Starting web UI - browser will open automatically...
python app.py