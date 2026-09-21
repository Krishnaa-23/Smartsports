@echo off
echo ===================================================
echo   Starting SmartSports V2 (FastAPI + React Frontend)
echo ===================================================

echo.
echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "SmartSports FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 > nul

echo.
echo [2/2] Starting React Frontend on http://localhost:5173 ...
start "SmartSports React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   SmartSports V2 is launching!
echo   - React UI:     http://localhost:5173
echo   - FastAPI Docs: http://localhost:8000/docs
echo   - Streamlit:    streamlit run app.py (preserved)
echo ===================================================
pause
