# Script PowerShell para iniciar o TechHelp Dashboard

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TechHelp Dashboard - Inicialização" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se o ambiente virtual existe
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "Execute setup.bat primeiro." -ForegroundColor Yellow
    pause
    exit 1
}

$pythonPath = ".\.venv\Scripts\python.exe"

Write-Host "[1/3] Iniciando Backend API (porta 5000)..." -ForegroundColor Green
$backend = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd api; & '$pythonPath' app.py" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "[2/3] Iniciando Frontend (porta 8080)..." -ForegroundColor Green
$frontend = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; & '$pythonPath' -m http.server 8080" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Dashboard Iniciado com Sucesso!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API:  http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend:     http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione CTRL+C em cada janela para parar os servidores" -ForegroundColor Yellow
Write-Host ""

Start-Sleep -Seconds 3

Write-Host "Abrindo dashboard no navegador..." -ForegroundColor Green
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "Dashboard pronto! Pressione qualquer tecla para sair..." -ForegroundColor Green
pause