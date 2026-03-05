@echo off
REM ============================================================================
REM Generate reports from existing profiling data
REM Use this if pytest already ran but report generation failed or was skipped
REM ============================================================================

echo.
echo === Generating Reports from Existing Profile Data ===
echo.

if not exist "docs\tests\performance_data\prof\durations.json" (
    echo ERROR: No profiling data found!
    echo Please run test_profiler.bat first to generate profile data.
    exit /b 1
)

echo Generating reports for slow tests...
python tools\test_profiler_plugin\generate_report.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Report generation failed!
    exit /b %errorlevel%
)

echo.
echo === Report Generation Complete ===
echo Output directory: docs\tests\performance_data\prof
echo.
