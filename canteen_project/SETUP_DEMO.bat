@echo off
echo ==========================================
echo   Campus Bites - Canteen Management System
echo   Demo Setup Script for New Laptop
echo ==========================================
echo.

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
echo.

echo [2/4] Setting up the database on this laptop...
echo NOTE: Make sure MySQL (XAMPP/WAMP) is running before continuing!
echo We are about to import the database.
set /p DBPASS="Please enter the MySQL root password for THIS laptop (leave empty if no password): "

if "%DBPASS%"=="" (
    echo Creating database and importing data without password...
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS canteen_db;"
    mysql -u root canteen_db < canteen_db_backup.sql
) else (
    echo Creating database and importing data...
    mysql -u root -p%DBPASS% -e "CREATE DATABASE IF NOT EXISTS canteen_db;"
    mysql -u root -p%DBPASS% canteen_db < canteen_db_backup.sql
    
    echo.
    echo ------------------------------------------
    echo IMPORTANT: If the password above is DIFFERENT from '107770', 
    echo Please open the '.env' file in Notepad and change 
    echo DB_PASSWORD=107770 to your new password right now!
    echo ------------------------------------------
    pause
)
echo.

echo [3/4] Running database migrations...
python manage.py migrate
echo.

echo [4/4] Starting server...
echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo Admin Login: admin / admin123 (OTP will be sent to campusbite654@gmail.com)
echo.
echo Starting server at http://127.0.0.1:8000
python manage.py runserver

pause
