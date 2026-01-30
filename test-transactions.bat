@echo off
REM ============================================
REM Generate Test Transactions
REM ============================================

echo ========================================
echo  Generating Test Transactions
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
echo Creating 5 test transactions for USR_10001...
echo.

python test_transactions_generator.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to generate test transactions
    pause
    exit /b 1
)

echo.
pause
