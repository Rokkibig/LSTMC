@echo off
REM Спеціалізоване перенавчання для M15 (15-хвилинний таймфрейм)
REM Рекомендується: ЩОДНЯ о 23:00 (коли день закінчився)
REM Причина: M15 швидко змінюється, потребує частого оновлення

cd /d "%~dp0"
call .venv\Scripts\activate

echo ========================================
echo   M15 СПЕЦІАЛІЗОВАНЕ ПЕРЕНАВЧАННЯ
echo   %date% %time%
echo ========================================
echo.
echo Використовує GRU (швидше) для M15
echo Фокус на свіжих даних
echo.

REM Використовуємо GRU (швидший за LSTM, але майже так само точний)
REM Без augmentation для M15 (багато real даних)
python scripts/train_lstm.py --config config.yaml --model-type gru --no-augment

REM Генеруємо свіжі сигнали
python scripts/infer_signals.py --config config.yaml

echo.
echo ========================================
echo   M15 ОНОВЛЕНО: %date% %time%
echo ========================================
