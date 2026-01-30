@echo off
REM ============================================
REM Health Check - Verify System Running
REM ============================================

echo ========================================
echo  System Health Check
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

python health_check_script.py

echo.
pause
