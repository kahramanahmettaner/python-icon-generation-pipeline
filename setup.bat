@echo off
setlocal enabledelayedexpansion

set VENV_NAME=icon-generation-pipeline

:: Check if Python is installed
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python is not installed or not added to PATH.
    echo Please install Python 3.6 or later and make sure it's available in the system PATH.
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment: %VENV_NAME%...
python -m venv %VENV_NAME%
IF ERRORLEVEL 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)

:: Activate virtual environment
call %VENV_NAME%\Scripts\activate

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
IF EXIST requirements.txt (
    echo Installing packages from requirements.txt...
    pip install -r requirements.txt
) ELSE (
    echo requirements.txt not found. Skipping package installation.
)

echo.
echo Setup complete.
echo To activate the virtual environment manually later, run:
echo %VENV_NAME%\Scripts\activate
pause
