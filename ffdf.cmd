@echo off
setlocal
set "FFDF_ROOT=%~dp0"
if "%FFDF_ROOT:~-1%"=="\" set "FFDF_ROOT=%FFDF_ROOT:~0,-1%"
set "PYTHONPATH=%FFDF_ROOT%\src;%PYTHONPATH%"
"%FFDF_ROOT%\.venv\Scripts\python.exe" -m financial_filing_data_foundation.user_cli %*
exit /b %ERRORLEVEL%
