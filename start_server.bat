@echo off
echo ========================================
echo    SecureAttend Pro - Starting Server
echo ========================================
echo.

cd /d "c:\Users\HARDIK\OneDrive\Desktop\project"

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

echo.
echo Installing/Updating dependencies...
pip install -r requirements.txt

echo.
echo Initializing database...
python -c "from app import app; from database.database import db; import sys; app.app_context().push(); result = db.connect(); db.create_tables() if result else None; db.insert_sample_data() if result else None; print('Database initialized successfully' if result else 'Database initialization failed'); sys.exit(0 if result else 1)"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Database initialization failed
    echo Please check your MySQL installation and configuration
    pause
    exit /b 1
)

echo.
echo ========================================
echo Starting Flask development server...
echo Application will be available at:
echo http://localhost:5000
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py

pause
