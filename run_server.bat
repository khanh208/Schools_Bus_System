@echo off
echo ================================================
echo Starting School Bus System
echo ================================================
echo.

REM Check virtual environment
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b
)

REM Start Redis
echo [1/4] Starting Redis Server...
start "Redis Server" redis-server
timeout /t 3
echo       Done!
echo.

REM Check Redis
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Redis failed to start!
    pause
    exit /b
)

REM Start Django Server
echo [2/4] Starting Django Server (Uvicorn)...
start "Django Server" cmd /k "venv\Scripts\activate && uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload --ws websockets"
timeout /t 5
echo       Done!
echo.

REM Start Celery Worker (với solo pool cho Windows)
echo [3/4] Starting Celery Worker...
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A config worker -l info --pool=solo"
timeout /t 3
echo       Done!
echo.

REM Start Celery Beat
echo [4/4] Starting Celery Beat...
start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A config beat -l info"
timeout /t 2
echo       Done!
echo.

echo ================================================
echo All services started successfully!
echo ================================================
echo.
echo URLs:
echo   - API: http://localhost:8000
echo   - Admin: http://localhost:8000/admin/
echo   - Swagger: http://localhost:8000/swagger/
echo   - Parent Tracking Demo: http://localhost:8000/api/tracking/parent/demo/
echo.
echo Login credentials:
echo   - Admin: admin / admin123
echo   - Parent: parent1 / parent123
echo   - Driver: driver1 / driver123
echo.
echo Press any key to open browser...
pause

start http://localhost:8000
npm run dev