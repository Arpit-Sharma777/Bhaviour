@echo off
REM ============================================
REM ALL-IN-ONE: Complete Setup & Run
REM ============================================

echo.
echo ========================================
echo  FRAUD DETECTION SYSTEM - AUTO SETUP
echo ========================================
echo.
echo This will:
echo   1. Setup virtual environment
echo   2. Install dependencies
echo   3. Start Redis
echo   4. Start API Server
echo   5. Generate test data
echo   6. Open browser
echo.
echo Prerequisites:
echo   ✓ Python 3.10+ (required)
echo   ✓ Redis Server (will check, run install-redis.bat if needed)
echo.
echo.
pause

REM Run setup
echo.
echo [STEP 1/5] Running setup...
call setup.bat

REM Clear screen and continue
cls
echo.
echo ========================================
echo  STARTING SERVICES
echo ========================================
echo.

REM Start Redis in new window
echo [STEP 2/5] Starting Redis...
start "Redis Server" cmd /k start-redis.bat

timeout /t 3 /nobreak

REM Start Server in new window
echo [STEP 3/5] Starting API Server...
start "API Server" cmd /k start-server.bat

timeout /t 5 /nobreak

REM Generate test data
echo [STEP 4/5] Generating test data...
call test-transactions.bat

cls
echo.
echo ========================================
echo  SETUP COMPLETE!
echo ========================================
echo.
echo Your fraud detection system is running!
echo.
echo OPEN IN BROWSER:
echo   http://localhost:8000/customer-profile
echo.
echo RUNNING SERVICES:
echo   • Redis Server (port 6379)
echo   • API Server (port 8000)
echo   • Test Data (5 transactions)
echo.
echo WINDOWS OPEN:
echo   • Redis Server (terminal)
echo   • API Server (terminal)
echo.
echo NEXT STEPS:
echo   1. Click the browser window that opened
echo   2. Or manually go to http://localhost:8000/customer-profile
echo   3. Enter: USR_10001
echo   4. Click: Load Profile
echo.
echo ========================================
echo.
pause

REM Open browser
call open-browser.bat
