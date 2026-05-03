@echo off
REM Kidwall Auto-Startup Batch Wrapper
REM Double-click this file to start all services

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-all.ps1"
pause
