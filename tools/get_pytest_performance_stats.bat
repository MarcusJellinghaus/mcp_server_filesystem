@echo off
REM Pytest Performance Statistics
REM Runs pytest with duration reporting for the 50 slowest tests
REM Outputs to timestamped file in docs/tests/performance_data/

REM Create timestamp for filename
for /f "tokens=2 delims==:" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "SS=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%SS%"

REM Create output directory if it doesn't exist
if not exist "docs\tests\performance_data" mkdir "docs\tests\performance_data"

REM Set output file
set "output_file=docs\tests\performance_data\performance_stats_%timestamp%.txt"

REM Get git branch
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set "git_branch=%%i"
if "%git_branch%"=="" set "git_branch=unknown"

echo === PYTEST PERFORMANCE REPORT === > "%output_file%"
echo === PYTEST PERFORMANCE REPORT ===
echo Timestamp: %YYYY%-%MM%-%DD% %HH%:%Min%:%SS%
echo Timestamp: %YYYY%-%MM%-%DD% %HH%:%Min%:%SS% >> "%output_file%"
echo Git Branch: %git_branch%
echo Git Branch: %git_branch% >> "%output_file%"
echo.
echo. >> "%output_file%"

echo ========================================
echo ========================================>> "%output_file%"
echo ALL TESTS - 50 slowest durations
echo ALL TESTS - 50 slowest durations >> "%output_file%"
echo ========================================
echo ========================================>> "%output_file%"
echo EXECUTION MODE: Parallel (-n auto)
echo EXECUTION MODE: Parallel (-n auto) >> "%output_file%"
echo.
echo. >> "%output_file%"

set "temp_file=%temp%\pytest_output_%random%.txt"
pytest --durations=50 -n auto -q --tb=no --no-header -p no:warnings 2>nul | findstr /R "[0-9].*s" > "%temp_file%"
type "%temp_file%"
type "%temp_file%" >> "%output_file%"
del "%temp_file%" 2>nul

echo.
echo.>> "%output_file%"
echo ========================================
echo ========================================>> "%output_file%"
echo Performance statistics collection complete!
echo Performance statistics collection complete! >> "%output_file%"
echo Output saved to: %output_file%
echo Output saved to: %output_file% >> "%output_file%"
echo ========================================
echo ========================================>> "%output_file%"
