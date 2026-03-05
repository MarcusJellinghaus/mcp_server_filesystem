@echo off
REM Run tach architecture boundary checks

echo Running tach...
tach check

if %errorlevel% neq 0 (
    echo.
    echo ✗ Tach found architectural violations!
    exit /b 1
)

echo.
echo ✓ All architectural boundaries respected!
