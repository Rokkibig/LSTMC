@echo off
echo ========================================
echo   AUTO-RETRAIN DAEMON
echo ========================================
echo.
echo This will run automatic retraining every 24 hours
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
call .venv\Scripts\activate
python auto_retrain_daemon.py

pause
