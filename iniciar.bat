@echo off
cd /d "%~dp0"

echo ==========================================
echo      Iniciando Sistema de Emprestimos
echo ==========================================

echo.
echo 1. Iniciando o servidor Backend...
start "Backend API - NAO FECHE ESTA JANELA" cmd /k "cd backend && uvicorn main:app --reload"

echo.
echo Aguardando o servidor iniciar (5 segundos)...
timeout /t 5 > nul

echo.
echo 2. Abrindo o Frontend no navegador...
start frontend/index.html

echo.
echo ==========================================
echo      Sistema iniciado com sucesso!
echo ==========================================
echo.
echo Para encerrar, feche a janela do servidor Backend e o navegador.
echo.
pause
