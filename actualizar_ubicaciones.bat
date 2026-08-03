@echo off
REM Script para actualizar ubicaciones de activos desde CSV
REM Configurar variables de entorno para MySQL


echo ======================================================================
echo SCRIPT DE ACTUALIZACION DE UBICACIONES - JEROSMART ACTIVOS
echo ======================================================================
echo.
echo Configuracion MySQL:
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
