@echo off
REM ============================================
REM Open All Interfaces in Browser
REM ============================================

echo ========================================
echo  Opening Fraud Detection System
echo ========================================
echo.
echo Opening in browser...
echo.

timeout /t 1 /nobreak

REM Main UI
echo [1/3] Opening Main UI...
start http://localhost:8000/

timeout /t 2 /nobreak

REM Admin Dashboard
echo [2/3] Opening Admin Dashboard...
start http://localhost:8000/admin

timeout /t 2 /nobreak

REM Customer Profiles
echo [3/3] Opening Customer Profiles...
start http://localhost:8000/customer-profile

echo.
echo ========================================
echo ✅ All windows opened!
echo ========================================
echo.
echo URLS:
echo   Main UI:              http://localhost:8000/
echo   Admin Dashboard:      http://localhost:8000/admin
echo   Customer Profiles:    http://localhost:8000/customer-profile
echo.
