@echo off
cd /d "%~dp0"
set "PY="

if exist "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe" (
  set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
)
if not defined PY (
  python -c "print(1)" >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo [ERROR] Python 3.10+ not found. Install Python first.
  pause
  exit /b 1
)

echo [1/2] Installing PyInstaller...
%PY% -m pip install pyinstaller
echo [2/2] Building exe (1-2 min)...
%PY% -m PyInstaller --onefile --name LegalReader --add-data "index.html;." server.py
echo.
echo Done. See dist\LegalReader.exe
pause
