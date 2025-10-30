@echo off
REM Script para executar o TechHelp Dashboard no Windows

echo 🚀 Iniciando TechHelp Dashboard...

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

REM Cria ambiente virtual se não existir
if not exist "venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

REM Ativa ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instala dependências
echo 📋 Instalando dependências...
pip install -r api\requirements.txt

REM Verifica se arquivo de configuração existe
if not exist "config\.env" (
    echo ⚙️ Criando arquivo de configuração...
    copy config\.env.example config\.env
    echo ⚠️ Configure o arquivo config\.env com suas credenciais do Google
)

REM Verifica credenciais do Google
if not exist "config\service-account.json" (
    echo ⚠️ Arquivo de credenciais não encontrado!
    echo 📝 Siga as instruções em config\service-account.json.example
    echo 🔗 Configure as credenciais do Google Cloud Console
)

echo.
echo ✅ Configuração concluída!
echo.
echo 📝 Para executar:
echo 1. Backend API: cd api ^&^& python app.py
echo 2. Frontend: cd frontend ^&^& python -m http.server 8080
echo.
echo 🌐 Acesse: http://localhost:8080
echo.

pause