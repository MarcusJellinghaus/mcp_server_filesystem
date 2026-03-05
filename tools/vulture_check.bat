@echo off
REM Run vulture dead code detection

echo Running vulture...
vulture src tests vulture_whitelist.py --min-confidence 60

if %errorlevel% neq 0 (
    echo.
    echo ✗ Vulture found unused code!
    exit /b 1
)

echo.
echo ✓ No dead code found!
