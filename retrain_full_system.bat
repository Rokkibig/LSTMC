@echo off

echo [STEP 0/5] Deleting old meta-models to ensure a clean retrain...
del /Q models\meta_model_*.joblib

echo [STEP 1/5] Retraining base models...
python scheduler.py
if %errorlevel% neq 0 (
    echo [ERROR] Step 1 failed. Aborting.
    exit /b %errorlevel%
)

echo [STEP 2/5] Generating new history with new features (this will take a long time)...
python historical_generator.py --config config.yaml
if %errorlevel% neq 0 (
    echo [ERROR] Step 2 failed. Aborting.
    exit /b %errorlevel%
)

echo [STEP 3/5] Creating new meta-dataset...
python label_generator.py
if %errorlevel% neq 0 (
    echo [ERROR] Step 3 failed. Aborting.
    exit /b %errorlevel%
)

echo [STEP 4/5] Retraining meta-models on new data...
python train_meta_model.py
if %errorlevel% neq 0 (
    echo [ERROR] Step 4 failed. Aborting.
    exit /b %errorlevel%
)

echo [SUCCESS] Full system retraining complete.
pause
