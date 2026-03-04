@echo off
REM Run mypy type checking

echo Running mypy (strict mode)...
mypy --strict src tests

if %errorlevel% neq 0 (
    echo.
    echo ✗ Mypy found type errors!
    exit /b 1
)

echo.
echo ✓ No mypy errors found!
