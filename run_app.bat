@echo off
TITLE Delhivery AI Assistant Launcher

echo ===================================================
echo   Starting Delhivery AI Assistant Services...
echo ===================================================

:: 1. Activate Virtual Environment
call .venv\Scripts\activate.bat

:: 2. Start FastAPI Backend in a new terminal window
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "FastAPI Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Pause briefly to ensure backend initializes
timeout /t 3 /nobreak > nul

:: 3. Start Streamlit UI in a new terminal window
echo [2/2] Starting Streamlit UI...
start "Streamlit UI" cmd /k "call .venv\Scripts\activate.bat && streamlit run app.py"

echo ===================================================
echo   All services launched successfully!
echo ===================================================