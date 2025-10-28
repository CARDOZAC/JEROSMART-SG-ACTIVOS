@echo off
chcp 65001 >nul

echo --------------------------------------------
echo 🛑 CERRANDO TODOS LOS PROCESOS PYTHON...
taskkill /F /IM python.exe >nul 2>&1

echo --------------------------------------------
echo ✅ TODOS LOS PROCESOS PYTHON FINALIZADOS.
pause