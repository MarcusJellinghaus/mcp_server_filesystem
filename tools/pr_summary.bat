@echo off
setlocal enabledelayedexpansion

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not in a git repository
    exit /b 1
)

REM Detect default branch or use environment variable
if defined BASE_BRANCH (
    set DEFAULT_BRANCH=%BASE_BRANCH%
) else (
    REM Try to detect the default branch from origin
    for /f "tokens=3" %%i in ('git symbolic-ref refs/remotes/origin/HEAD 2^>nul') do (
        for /f "tokens=2 delims=/" %%j in ("%%i") do set DEFAULT_BRANCH=%%j
    )
    REM Fallback to common defaults if detection fails
    if not defined DEFAULT_BRANCH (
        git rev-parse --verify origin/main >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            set DEFAULT_BRANCH=main
        ) else (
            git rev-parse --verify origin/master >nul 2>&1
            if %ERRORLEVEL% EQU 0 (
                set DEFAULT_BRANCH=master
            ) else (
                echo Error: Could not detect default branch. Set BASE_BRANCH environment variable.
                exit /b 1
            )
        )
    )
)

echo Using base branch: %DEFAULT_BRANCH%

REM Check if PR_Info folder exists, create if not
if not exist PR_Info (
    echo Creating PR_Info folder...
    mkdir PR_Info
)

REM Create temporary file with unique name for large diffs
set TEMP_FILE=%TEMP%\pr_summary_%RANDOM%_%TIME:~6,2%%TIME:~9,2%.txt

REM Generate git diff and create PR summary prompt
(
    echo Please read the information in folder `PR_Info` ^(if any^) and review the code changes ^(git output^)
    echo Can you please create a limited size summary for a pull request?
    echo Please do not refer to the files in `PR_Info` directly !
    echo Please save the pull request summary in markdown file ^(as `PR_Info\summary.md`^) so that I can easily copy/paste it.
    echo Last step, delete all files from folder `PR_Info`
    echo.
    echo === GIT DIFF ===
    echo.
    git diff --unified=5 --no-prefix %DEFAULT_BRANCH%...HEAD
) > %TEMP_FILE%

REM Check file size (warn if > 500KB)
for %%A in ("%TEMP_FILE%") do set FILE_SIZE=%%~zA
if %FILE_SIZE% GTR 512000 (
    echo Warning: Diff is large ^(%FILE_SIZE% bytes^). Clipboard may have limitations.
)

REM Copy to clipboard
type %TEMP_FILE% | clip

REM Clean up
del %TEMP_FILE%

echo PR summary prompt with git diff copied to clipboard!
echo Paste it in the LLM to generate a pull request summary.
exit /b 0
