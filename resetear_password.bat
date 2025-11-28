@echo off
REM =====================================================================
REM SCRIPT: Resetear contraseña del admin
REM Descripción: Resetea la contraseña a '12345'
REM =====================================================================

echo.
echo ========================================
echo RESET DE CONTRASENA - ADMIN
echo ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Ejecutando reset de contrasena...
echo.

python reset_password.py

echo.
echo ========================================
echo.
echo Si viste el mensaje "La contrasena funciona correctamente"
echo ya puedes iniciar sesion con:
echo.
echo Email:      activosfijos@clinicaprimavera.com
echo Contrasena: 12345
echo.
echo ========================================
echo.

pause
