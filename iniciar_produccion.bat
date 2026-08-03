@echo off
REM ===================================================================
REM  SG Activos Fijos - Inicio en modo PRODUCCION (Waitress)
REM
REM  A diferencia de iniciar_app.bat, que usa el servidor de desarrollo
REM  de Flask, este arranca Waitress: aguanta varios usuarios a la vez
REM  y no expone el depurador de Werkzeug.
REM
REM  Las credenciales se leen de .env (no se escriben aqui).
REM ===================================================================
title SG Activos Fijos - Servidor

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo ERROR: no se encontro el entorno virtual en venv\
    echo Crealo con:  python -m venv venv
    echo Luego:       venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo ERROR: no existe el archivo .env
    echo Copia .env.example como .env y completa los datos de conexion.
    echo.
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo   Iniciando SG Activos Fijos
echo ===================================================================
echo.
echo   Local:  http://localhost:5000
echo   Red:    consulta tu IP con ipconfig
echo.
echo   Para detener el servidor: Ctrl+C
echo   Registro de actividad:    logs\jerosmart.log
echo.
echo ===================================================================
echo.

venv\Scripts\python.exe serve.py

echo.
echo El servidor se detuvo.
pause
