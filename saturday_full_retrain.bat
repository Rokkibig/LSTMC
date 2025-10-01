@echo off
REM Повне перенавчання в суботу (2-4 години)
REM Запускати в суботу о 02:00 (коли Forex закритий)

cd /d "%~dp0"
call .venv\Scripts\activate

echo ========================================
echo   ПОВНЕ СУББОТНЄ ПЕРЕНАВЧАННЯ
echo   %date% %time%
echo ========================================
echo.
echo Це займе 2-4 години...
echo.

python run_improved_pipeline.py --model-type ensemble --meta-ensemble --cv-folds 5

echo.
echo ========================================
echo   ЗАВЕРШЕНО: %date% %time%
echo ========================================
