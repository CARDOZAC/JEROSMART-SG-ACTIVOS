@echo off
chcp 65001 >nul

echo --------------------------------------------
echo 🛑 CERRANDO PROCESOS PYTHON...
taskkill /F /IM python.exe >nul 2>&1

echo ⏳ Esperando 2 segundos para liberar puerto...
timeout /T 2 >nul

echo --------------------------------------------
echo 🔄 INICIANDO NUEVAMENTE...
call iniciar.bat

echo --------------------------------------------
echo ✅ REINICIO COMPLETO.
pause