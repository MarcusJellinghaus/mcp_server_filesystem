@echo off
REM Generate architecture documentation (dependency graph and report)
REM
REM Usage from Git Bash: ./tools/tach_docs.sh
REM Usage from cmd.exe:  tools\tach_docs.bat
REM
REM Creates:
REM   - docs/architecture/dependency_graph.html
REM   - docs/architecture/dependency_report.html

python "%~dp0tach_docs.py" %*
exit /b %ERRORLEVEL%
