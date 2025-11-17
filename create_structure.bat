@echo off
echo Creating app structure...

REM Create migrations folders
mkdir apps\authentication\migrations 2>nul
mkdir apps\students\migrations 2>nul
mkdir apps\routes\migrations 2>nul
mkdir apps\attendance\migrations 2>nul
mkdir apps\tracking\migrations 2>nul
mkdir apps\notifications\migrations 2>nul
mkdir apps\reports\migrations 2>nul
mkdir apps\backup\migrations 2>nul

REM Create __init__.py for apps
type nul > apps\__init__.py
type nul > apps\authentication\__init__.py
type nul > apps\students\__init__.py
type nul > apps\routes\__init__.py
type nul > apps\attendance\__init__.py
type nul > apps\tracking\__init__.py
type nul > apps\notifications\__init__.py
type nul > apps\reports\__init__.py
type nul > apps\backup\__init__.py

REM Create __init__.py for migrations
type nul > apps\authentication\migrations\__init__.py
type nul > apps\students\migrations\__init__.py
type nul > apps\routes\migrations\__init__.py
type nul > apps\attendance\migrations\__init__.py
type nul > apps\tracking\migrations\__init__.py
type nul > apps\notifications\migrations\__init__.py
type nul > apps\reports\migrations\__init__.py
type nul > apps\backup\migrations\__init__.py

REM Create apps.py files
echo from django.apps import AppConfig > apps\authentication\apps.py
echo. >> apps\authentication\apps.py
echo class AuthenticationConfig(AppConfig): >> apps\authentication\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\authentication\apps.py
echo     name = 'apps.authentication' >> apps\authentication\apps.py

echo from django.apps import AppConfig > apps\students\apps.py
echo. >> apps\students\apps.py
echo class StudentsConfig(AppConfig): >> apps\students\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\students\apps.py
echo     name = 'apps.students' >> apps\students\apps.py

echo from django.apps import AppConfig > apps\routes\apps.py
echo. >> apps\routes\apps.py
echo class RoutesConfig(AppConfig): >> apps\routes\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\routes\apps.py
echo     name = 'apps.routes' >> apps\routes\apps.py

echo from django.apps import AppConfig > apps\attendance\apps.py
echo. >> apps\attendance\apps.py
echo class AttendanceConfig(AppConfig): >> apps\attendance\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\attendance\apps.py
echo     name = 'apps.attendance' >> apps\attendance\apps.py

echo from django.apps import AppConfig > apps\tracking\apps.py
echo. >> apps\tracking\apps.py
echo class TrackingConfig(AppConfig): >> apps\tracking\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\tracking\apps.py
echo     name = 'apps.tracking' >> apps\tracking\apps.py

echo from django.apps import AppConfig > apps\notifications\apps.py
echo. >> apps\notifications\apps.py
echo class NotificationsConfig(AppConfig): >> apps\notifications\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\notifications\apps.py
echo     name = 'apps.notifications' >> apps\notifications\apps.py

echo from django.apps import AppConfig > apps\reports\apps.py
echo. >> apps\reports\apps.py
echo class ReportsConfig(AppConfig): >> apps\reports\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\reports\apps.py
echo     name = 'apps.reports' >> apps\reports\apps.py

echo from django.apps import AppConfig > apps\backup\apps.py
echo. >> apps\backup\apps.py
echo class BackupConfig(AppConfig): >> apps\backup\apps.py
echo     default_auto_field = 'django.db.models.BigAutoField' >> apps\backup\apps.py
echo     name = 'apps.backup' >> apps\backup\apps.py

echo.
echo ✓ Structure created successfully!
echo.
echo Next steps:
echo   1. python manage.py makemigrations
echo   2. python manage.py migrate
echo.
pause