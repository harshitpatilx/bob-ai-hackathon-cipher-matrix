@echo off
REM CFNA - Bob-powered Cyber Fraud Network Analyzer
REM Double-click this file to open the input form in your browser.
REM Any arguments are passed straight through, e.g.  start_cfna.bat --port 9000
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH. Install Python 3.10+ and try again.
  pause
  exit /b 1
)

echo Starting CFNA ...
echo   Close this window (or press Ctrl+C) to stop.
python -m cfna serve %*
pause
