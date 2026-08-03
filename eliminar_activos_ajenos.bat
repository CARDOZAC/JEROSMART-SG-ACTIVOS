@echo off
REM Script para eliminar todos los activos ajenos de la base de datos


echo ======================================================================
echo ELIMINAR ACTIVOS AJENOS - JEROSMART ACTIVOS
echo ======================================================================
echo.
echo Configuracion MySQL:
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
