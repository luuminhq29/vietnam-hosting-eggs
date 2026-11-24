@echo off
setlocal
set "REPO_ROOT=%~dp0.."
set "PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%"
python -m generator %*
exit /b %ERRORLEVEL%
