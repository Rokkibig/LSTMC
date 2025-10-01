@echo off
REM Швидкий тест покращеного pipeline
REM Використовує GRU (швидший), без augmentation, без historical generation

echo ========================================
echo   ШВИДКИЙ ТЕСТ ПОКРАЩЕНЬ
echo ========================================
echo.

python run_improved_pipeline.py --fast-mode --skip-fetch

echo.
echo ========================================
echo   ТЕСТ ЗАВЕРШЕНО
echo ========================================
pause
