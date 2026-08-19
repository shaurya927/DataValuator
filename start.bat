@echo off
setlocal

echo =========================================
echo    Starting DataValuator Environment
echo =========================================
echo.

:: Navigate to the directory where this script is located
cd /d "%~dp0"

:: 1. Check Prerequisites
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in your PATH.
    echo Please install Node.js and try again.
    pause
    exit /b
)

:: 2. Backend Setup & Start
echo [1/3] Setting up Backend...
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    python -m venv backend\venv
    call backend\venv\Scripts\activate.bat
    echo Installing backend dependencies...
    pip install -r backend\requirements.txt
) else (
    call backend\venv\Scripts\activate.bat
)

echo Starting backend server in a background window...
start "DataValuator Backend" /MIN cmd /c "call backend\venv\Scripts\activate.bat && cd backend && python run.py"

:: 3. Frontend Setup & Start
echo [2/3] Setting up Frontend...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo Starting frontend server in a background window...
start "DataValuator Frontend" /MIN cmd /c "npm run dev"
cd ..

:: 4. Open Browser
echo [3/3] Opening Browser...
echo Waiting 5 seconds for servers to initialize...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo =========================================
echo DataValuator is now running! 
echo Two minimized command windows have been opened for the servers.
echo You can safely close this window. To stop the application later, 
echo simply close the two minimized "DataValuator Backend" and 
echo "DataValuator Frontend" command prompt windows.
echo =========================================
echo.
pause
