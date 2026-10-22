@echo off
cd /d "%~dp0"
set "PY="

if exist "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
  set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)
if not defined PY (
  py -3 -c "print(1)" >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  python -c "print(1)" >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo [ERROR] Python 3.10+ not found.
  echo Install from https://www.python.org/downloads/ then re-run this script.
  pause
  exit /b 1
)

echo Starting LegalReader...
%PY% server.py
pause
