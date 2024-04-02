@echo off

REM Check if Python is installed
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python could not be found. Please install Python 3.
    exit /b
)

REM Install necessary Python packages
python -m pip install --upgrade pip
python -m pip install flask flask_sqlalchemy transformers diffusers torch pillow

REM Check for LUCRA_AI_QUERIES_DATABASE_URI environment variable
IF NOT DEFINED LUCRA_AI_QUERIES_DATABASE_URI (
    echo LUCRA_AI_QUERIES_DATABASE_URI environment variable is not set. Please set it.
    exit /b
)

REM Start the Python application
python main.py