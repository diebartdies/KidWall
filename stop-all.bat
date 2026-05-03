@echo off
REM Kidwall Stop All Services

echo.
echo ========================================
echo Kidwall Project - Stop All Services
echo ========================================
echo.

docker-compose down --remove-orphans

echo.
echo All services stopped
echo.
pause
