@echo off
REM MT5 Data Provider - Легкий API для віддачі даних Linux серверу
REM Порт: 5000

cd /d "%~dp0\.."
call .venv\Scripts\activate

echo ========================================
echo   MT5 DATA PROVIDER
echo   Starting on port 5000
echo ========================================
echo.

python windows/mt5_data_provider.py

pause
