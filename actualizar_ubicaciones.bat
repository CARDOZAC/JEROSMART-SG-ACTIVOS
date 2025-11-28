@echo off
REM Script para actualizar ubicaciones de activos desde CSV
REM Configurar variables de entorno para MySQL

set DB_TYPE=mysql
set DB_USER=root
set DB_PASSWORD=JeroNimoDaviLex9824.
set DB_NAME=jerosmart_activos
set DB_HOST=localhost
set DB_PORT=3306

echo ======================================================================
echo SCRIPT DE ACTUALIZACION DE UBICACIONES - JEROSMART ACTIVOS
echo ======================================================================
echo.
echo Configuracion MySQL:
echo   Usuario: %DB_USER%
echo   Base de datos: %DB_NAME%
echo   Host: %DB_HOST%:%DB_PORT%
echo.
echo ======================================================================
echo.

REM Ejecutar el script Python
venv\Scripts\python.exe actualizar_ubicaciones.py "C:\Users\david\Downloads\ajenos200.csv"

echo.
echo ======================================================================
echo PROCESO COMPLETADO
echo ======================================================================
echo.
pause
