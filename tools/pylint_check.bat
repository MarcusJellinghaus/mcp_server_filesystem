@echo off
REM Run pylint error check

echo Running pylint (errors only)...
pylint -E ./src ./tests

if %errorlevel% neq 0 (
    echo.
    echo ✗ Pylint found errors!
    exit /b 1
)

echo.
echo ✓ No pylint errors found!
