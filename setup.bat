@echo off
REM Setup script for Travel Planning Assistant Backend (Windows)

echo ================================
echo Travel Planning Assistant Setup
echo ================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    exit /b 1
)

echo [1/5] Creating virtual environment...
cd backend
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo [4/5] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it with your API keys.
) else (
    echo .env file already exists.
)

echo [5/5] Setup complete!
echo.
echo ================================
echo Next steps:
echo ================================
echo 1. Edit backend\.env and add your API keys
echo 2. Run: cd backend
echo 3. Run: .venv\Scripts\activate
echo 4. Run: python main.py
echo.
echo Or run the test script: python test_backend.py
echo.
echo API will be available at: http://127.0.0.1:8000
echo API docs at: http://127.0.0.1:8000/docs
echo ================================

cd ..
