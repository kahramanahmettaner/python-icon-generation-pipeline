@echo off

set VENV_NAME=icon-generation-pipeline

:: Check if virtual environment exists
IF NOT EXIST "%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call %VENV_NAME%\Scripts\activate

:: Run the main script
python main.py

pause
