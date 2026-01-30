@echo off
REM ============================================
REM Start Redis - Run in separate window
REM ============================================

echo ========================================
echo  Starting Redis Server
echo ========================================
echo.

REM Check if redis-server exists at C:\redis
if not exist "C:\redis\redis-server.exe" (
    echo.
    echo ERROR: Redis is not installed at C:\redis
    echo.
    echo Please run: install-redis.bat
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Starting Redis Server...
echo.

"C:\redis\redis-server.exe"

echo.
echo ========================================
echo ✅ Redis is running on port 6379
echo ========================================
echo.
pause
