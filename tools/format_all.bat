@echo off
REM Format all Python code with black and isort

echo Running isort...
isort --profile=black --float-to-top src tests
if %errorlevel% neq 0 (
    echo ERROR: isort failed
    exit /b 1
)

echo Running black...
black src tests
if %errorlevel% neq 0 (
    echo ERROR: black failed
    exit /b 1
)

echo.
echo ✓ Formatting complete!
