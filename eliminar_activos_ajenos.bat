@echo off
REM Script para eliminar todos los activos ajenos de la base de datos

set DB_TYPE=mysql
set DB_USER=root
set DB_PASSWORD=JeroNimoDaviLex9824.
set DB_NAME=jerosmart_activos
set DB_HOST=localhost
set DB_PORT=3306

echo ======================================================================
echo ELIMINAR ACTIVOS AJENOS - JEROSMART ACTIVOS
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
venv\Scripts\python.exe eliminar_activos_ajenos.py

echo.
echo ======================================================================
echo PROCESO COMPLETADO
echo ======================================================================
echo.
pause
