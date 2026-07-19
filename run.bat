@echo off
TITLE PglRobot 2.0
echo Starting PglRobot...

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. 
    echo Please create it first by running: python -m venv .venv
    echo And install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
python -m PglRobot

echo.
echo [INFO] Bot process has stopped.
pause
