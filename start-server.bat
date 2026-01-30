@echo off
REM ============================================
REM Start Server - Run in separate window
REM ============================================

echo ========================================
echo  Starting Fraud Detection API Server
echo ========================================
echo.

cd /d c:\PROJECTS\ANAMOLY\Bhaviour

call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo.
echo Starting server on http://localhost:8000
echo Press CTRL+C to stop the server
echo.
echo ========================================
echo.

python -m uvicorn fraud_api:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start
    pause
    exit /b 1
)

pause
