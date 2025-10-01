@echo off
REM Щоденне швидке перенавчання (30 хвилин)
REM Запускати о 01:00 кожен день

cd /d "%~dp0"
call .venv\Scripts\activate

echo ========================================
echo   ЩОДЕННЕ ШВИДКЕ ПЕРЕНАВЧАННЯ
echo   %date% %time%
echo ========================================
echo.

python run_improved_pipeline.py --skip-history

echo.
echo ========================================
echo   ЗАВЕРШЕНО: %date% %time%
echo ========================================
