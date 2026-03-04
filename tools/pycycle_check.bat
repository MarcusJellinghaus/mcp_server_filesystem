@echo off
REM Run pycycle circular dependency detection

echo Running pycycle...
pycycle --here

if %errorlevel% neq 0 (
    echo.
    echo ✗ Pycycle found circular dependencies!
    exit /b 1
)

echo.
echo ✓ No circular dependencies found!
