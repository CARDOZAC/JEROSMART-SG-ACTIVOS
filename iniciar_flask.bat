@echo off
REM =====================================================================
REM SCRIPT: Iniciar Flask con acceso desde red local
REM Descripción: Detiene cualquier proceso en puerto 5000 e inicia Flask
REM Fecha: 2025-11-19
REM =====================================================================

echo ========================================
echo INICIAR FLASK - JEROSMART ACTIVOS
echo ========================================
echo.

REM Ir al directorio del proyecto
cd /d "%~dp0"

echo Verificando si hay proceso en puerto 5000...
echo.

REM Buscar proceso en puerto 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    set PID=%%a
)

if defined PID (
    echo Se encontro proceso en puerto 5000 (PID: %PID%)
    echo Deteniendo proceso...
    taskkill /PID %PID% /F >nul 2>&1
    echo Proceso detenido.
    echo.
    timeout /t 2 >nul
) else (
    echo Puerto 5000 esta libre.
    echo.
)

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo.
)

REM Obtener IP local
echo Obteniendo direccion IP local...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"Dirección IPv4"') do (
    set IP=%%a
)

REM Limpiar espacios de la IP
set IP=%IP: =%

echo.
echo ========================================
echo INICIANDO SERVIDOR FLASK
echo ========================================
echo.
echo Puerto: 5000
echo IP Local: %IP%
echo.
echo Accede desde tu celular usando:
echo http://%IP%:5000
echo.
echo ========================================
echo.

REM Iniciar Flask
python run.py

pause
