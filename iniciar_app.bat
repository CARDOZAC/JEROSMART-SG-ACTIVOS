@echo off
title Panel de Control - SIG Activos Fijos
chcp 65001 >nul

:: Establecer el punto de entrada de la aplicación Flask
set FLASK_APP=run.py
set FLASK_ENV=development

:: Ruta al entorno virtual
set VENV_PATH=%~dp0venv\Scripts\activate

:MENU
cls
echo.
echo =======================================================
echo    PANEL DE CONTROL - GESTION DE ACTIVOS FIJOS
echo =======================================================
echo.
echo   [1] Iniciar Servidor de la Aplicacion
echo.
echo   [2] (Re)Inicializar la Base de Datos (CUIDADO: BORRA TODO)
echo   [3] Ejecutar Migracion de Datos desde CSV
echo.
echo   [4] Salir
echo.
echo -------------------------------------------------------
set /p "CHOICE=Elige una opcion y presiona Enter: "

if "%CHOICE%"=="1" goto start_server
if "%CHOICE%"=="2" goto init_db
if "%CHOICE%"=="3" goto migrate_data
if "%CHOICE%"=="4" goto exit
goto MENU

:start_server
cls
echo.
echo ✅ [1] INICIANDO SERVIDOR DE LA APLICACION...
echo --------------------------------------------
echo Activando entorno virtual...
call "%VENV_PATH%"
echo.
echo.
flask run --host=0.0.0.0
echo.
echo --------------------------------------------
echo Servidor detenido.
pause
goto MENU

:init_db
cls
echo.
echo ⚠️ [2] INICIALIZANDO BASE DE DATOS...
echo --------------------------------------------
echo ESTA ACCION BORRARA TODOS LOS DATOS EXISTENTES.
set /p "CONFIRM=Estas seguro de continuar? (S/N): "
if /I not "%CONFIRM%"=="S" goto MENU

echo Activando entorno virtual...
call "%VENV_PATH%"
echo Ejecutando script de inicializacion...
flask init-db
echo.
echo --------------------------------------------
echo Base de datos inicializada.
pause
goto MENU

:migrate_data
cls
echo.
echo 🚚 [3] EJECUTANDO MIGRACION DE DATOS...
echo --------------------------------------------
echo Este script importara los datos desde 'inventario_maestro.csv'.
echo Asegurate de que el archivo este preparado y en la carpeta correcta.
echo.
set /p "CONFIRM=Deseas continuar? (S/N): "
if /I not "%CONFIRM%"=="S" goto MENU

echo Activando entorno virtual...
call "%VENV_PATH%"
echo Ejecutando script de migracion...
python migracion.py
echo.
echo --------------------------------------------
echo Proceso de migracion finalizado.
pause
goto MENU

:exit
exit