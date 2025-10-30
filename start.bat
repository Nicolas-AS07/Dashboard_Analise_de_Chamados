@echo off
REM Script para iniciar o TechHelp Dashboard completo

echo.
echo ========================================
echo   TechHelp Dashboard - Inicializacao
echo ========================================
echo.

REM Verifica se o ambiente virtual existe
if not exist ".venv" (
    echo [ERROR] Ambiente virtual nao encontrado!
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

echo [1/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo [2/3] Iniciando Backend API (porta 5000)...
start "TechHelp Backend" cmd /k "cd api && ..\\.venv\\Scripts\\python.exe app.py"

timeout /t 3 /nobreak >nul

echo [3/3] Iniciando Frontend (porta 8080)...
start "TechHelp Frontend" cmd /k "cd frontend && ..\\.venv\\Scripts\\python.exe -m http.server 8080"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Dashboard Iniciado com Sucesso!
echo ========================================
echo.
echo Backend API:  http://localhost:5000
echo Frontend:     http://localhost:8080
echo.
echo Pressione CTRL+C em cada janela para parar os servidores
echo.

REM Abre o navegador automaticamente
timeout /t 3 /nobreak >nul
start http://localhost:8080

echo Dashboard aberto no navegador!
echo.
pause