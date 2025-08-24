@echo off
setlocal enabledelayedexpansion

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not in a git repository
    exit /b 1
)

REM Create temporary file for output with unique name
set TEMP_FILE=%TEMP%\commit_summary_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Generate git diff including untracked files by adding them with --intent-to-add
echo Please review the following code changes and create a concise commit message. > %TEMP_FILE%
echo The commit message should follow conventional commit format: >> %TEMP_FILE%
echo - First line: type/scope: brief description - max 50 chars >> %TEMP_FILE%
echo - Optional body: detailed explanation if needed >> %TEMP_FILE%
echo - Focus on WHAT changed and WHY, not HOW >> %TEMP_FILE%
echo. >> %TEMP_FILE%
echo Example format: feat/auth: add user login validation >> %TEMP_FILE%
echo. >> %TEMP_FILE%
echo === GIT STATUS === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git status --short >> %TEMP_FILE%
echo. >> %TEMP_FILE%

REM Add untracked files with intent-to-add to make them visible in diff
echo Adding untracked files for preview...
git add --intent-to-add .
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to add files for preview
    del %TEMP_FILE%
    exit /b 1
)

echo === GIT DIFF (ALL CHANGES INCLUDING NEW FILES) === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git diff --unified=5 --no-prefix >> %TEMP_FILE%

echo === GIT DIFF (STAGED FILES) === >> %TEMP_FILE%
echo. >> %TEMP_FILE%
git diff --cached --unified=5 --no-prefix >> %TEMP_FILE%

REM Reset the intent-to-add so files remain untracked
echo Resetting file status...
git reset
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to reset git status. You may need to run 'git reset' manually
)

REM Copy to clipboard
type %TEMP_FILE% | clip

REM Clean up
del %TEMP_FILE%

echo.
echo ===================================================
echo Commit summary copied to clipboard!
echo Includes: modified files + new untracked files
echo Paste it in your LLM to generate a commit message
echo ===================================================
exit /b 0
