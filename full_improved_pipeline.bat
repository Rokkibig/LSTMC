@echo off
REM Повний покращений pipeline з усіма features
REM Включає: ensemble models, meta-ensemble, cross-validation, backtest

echo ========================================
echo   ПОВНИЙ ПОКРАЩЕНИЙ PIPELINE
echo ========================================
echo.
echo Це займе значний час (2-4+ години залежно від даних)
echo.
echo Натисніть Ctrl+C для скасування або будь-яку клавішу для продовження...
pause > nul

python run_improved_pipeline.py --model-type ensemble --meta-ensemble --cv-folds 5

echo.
echo ========================================
echo   PIPELINE ЗАВЕРШЕНО
echo ========================================
echo.
echo Для перегляду результатів запустіть:
echo   codex run web
echo.
pause
