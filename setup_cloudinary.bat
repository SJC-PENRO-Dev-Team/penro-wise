@echo off
echo ========================================
echo   Cloudinary Migration Setup
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Step 1: Installing dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Testing Cloudinary connection...
python manage.py shell -c "import cloudinary; print('Cloudinary configured:', cloudinary.config().cloud_name)"
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your Cloudinary credentials
echo 2. Run: python manage.py migrate_to_cloudinary --dry-run
echo 3. Run: python manage.py migrate_to_cloudinary
echo.
pause
