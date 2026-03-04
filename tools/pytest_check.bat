@echo off
REM Run pytest

echo Running pytest (parallel mode)...
pytest -n auto

if %errorlevel% neq 0 (
    echo.
    echo ✗ Tests failed!
    exit /b 1
)

echo.
echo ✓ All tests passed!
