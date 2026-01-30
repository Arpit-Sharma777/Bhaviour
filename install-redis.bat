@echo off
REM ============================================
REM Install Redis for Windows
REM ============================================

echo ========================================
echo  Installing Redis for Windows
echo ========================================
echo.

REM Check if already in PATH
where redis-server >nul 2>nul
if %errorlevel% equ 0 (
    echo.
    echo ✅ Redis is already installed!
    redis-cli --version
    echo.
    pause
    exit /b 0
)

echo Downloading Redis for Windows...
echo.

REM Create temp directory
if not exist "%TEMP%\redis-install" mkdir "%TEMP%\redis-install"
cd /d "%TEMP%\redis-install"

REM Download using PowerShell
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://github.com/microsoftarchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.zip', 'redis.zip')"

if errorlevel 1 (
    echo ERROR: Failed to download Redis
    echo.
    echo Please download manually from:
    echo https://github.com/microsoftarchive/redis/releases
    echo.
    pause
    exit /b 1
)

echo Extracting Redis...
powershell -Command "Expand-Archive -Path 'redis.zip' -DestinationPath 'redis' -Force"

echo.
echo Creating C:\redis directory...
if not exist "C:\redis" mkdir "C:\redis"

REM Copy files to C:\redis
echo Copying files...
xcopy redis\* C:\redis\ /E /Y

echo.
echo Adding C:\redis to system PATH...
echo This requires admin privileges.
echo.

REM Try to add to PATH using registry
powershell -Command "
try {
    [Environment]::SetEnvironmentVariable(
        'Path',
        [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';C:\redis',
        'Machine'
    )
    Write-Host '✅ Successfully added C:\redis to PATH'
} catch {
    Write-Host '⚠️  Cannot modify system PATH (requires admin)'
    Write-Host 'Add C:\redis to PATH manually via Environment Variables'
}
"

echo.
echo ========================================
echo ✅ Redis installation complete!
echo ========================================
echo.
echo Redis location: C:\redis
echo.
echo Verify installation by closing and reopening terminal, then run:
echo   redis-cli --version
echo   redis-cli ping
echo.
pause
