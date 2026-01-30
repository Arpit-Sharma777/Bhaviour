@echo off
REM ============================================
REM Setup Batch File - Run ONCE
REM ============================================
REM This file sets up the project for the first time

echo ========================================
echo  Fraud Detection System - SETUP
echo ========================================

cd /d c:\PROJECTS\ANAMOLY\Bhaviour

echo.
echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate venv
    pause
    exit /b 1
)

echo.
echo [3/4] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying installation...
python -c "import fastapi, pandas, xgboost, redis; print('✅ All dependencies OK')"
if errorlevel 1 (
    echo ERROR: Verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Run: start-redis.bat
echo 2. Run: start-server.bat
echo 3. Run: test-transactions.bat
echo 4. Open: http://localhost:8000/customer-profile
echo.
pause
