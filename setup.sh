#!/bin/bash

# Script para executar o TechHelp Dashboard localmente
# Certifique-se de ter Python 3.8+ instalado

echo "🚀 Iniciando TechHelp Dashboard..."

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8+ e tente novamente."
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📋 Instalando dependências..."
pip install -r api/requirements.txt

# Verifica se arquivo de configuração existe
if [ ! -f "config/.env" ]; then
    echo "⚙️ Criando arquivo de configuração..."
    cp config/.env.example config/.env
    echo "⚠️ Configure o arquivo config/.env com suas credenciais do Google"
fi

# Verifica credenciais do Google
if [ ! -f "config/service-account.json" ]; then
    echo "⚠️ Arquivo de credenciais não encontrado!"
    echo "📝 Siga as instruções em config/service-account.json.example"
    echo "🔗 Configure as credenciais do Google Cloud Console"
fi

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📝 Para executar:"
echo "1. Backend API: cd api && python app.py"
echo "2. Frontend: cd frontend && python -m http.server 8080"
echo ""
echo "🌐 Acesse: http://localhost:8080"
echo ""