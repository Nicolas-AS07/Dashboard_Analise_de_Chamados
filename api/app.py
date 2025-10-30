"""
TechHelp Dashboard - API Flask
Servidor backend para integração com Google Sheets e fornecimento de dados para o dashboard
"""
import os
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google_sheets import create_google_sheets_client


# Carrega variáveis de ambiente a partir do caminho absoluto do arquivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'config', '.env'))
print(f"🔧 Carregando .env de: {ENV_PATH} (existe? {os.path.exists(ENV_PATH)})")
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Configuração da aplicação Flask
app = Flask(__name__)

# Configuração CORS para permitir requisições do frontend
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:8080').split(',')
CORS(app, origins=cors_origins)

# Cache simples em memória (para evitar muitas chamadas à API do Google)
cache = {
    'data': None,
    'timestamp': None,
    'timeout': int(os.getenv('CACHE_TIMEOUT', 300))  # 5 minutos
}


def is_cache_valid():
    """Verifica se o cache ainda é válido"""
    if cache['data'] is None or cache['timestamp'] is None:
        return False
    
    return (datetime.now() - cache['timestamp']).seconds < cache['timeout']


def update_cache(data):
    """Atualiza o cache com novos dados"""
    cache['data'] = data
    cache['timestamp'] = datetime.now()


@app.route('/')
def home():
    """Endpoint raiz com informações da API"""
    return jsonify({
        'message': 'TechHelp Dashboard API',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': [
            'GET /api/chamados - Retorna dados dos chamados',
            'GET /api/health - Verifica status da API'
        ],
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/health')
def health_check():
    """Endpoint de verificação de saúde da API"""
    try:
        # Testa conexão com Google Sheets
        sheets_client = create_google_sheets_client()
        
        return jsonify({
            'status': 'healthy',
            'google_sheets': 'connected',
            'cache_valid': is_cache_valid(),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'google_sheets': 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/chamados')
def get_chamados():
    """
    Endpoint principal que retorna dados processados dos chamados
    Utiliza cache para otimizar performance
    """
    try:
        # Verifica se pode usar cache
        if is_cache_valid():
            print("📋 Dados servidos do cache")
            return jsonify(cache['data'])
        
        print("🔄 Buscando dados atualizados do Google Sheets/Drive...")
        
        # Cria cliente Google Sheets
        sheets_client = create_google_sheets_client()
        
        # Processa dados da planilha
        data = sheets_client.process_chamados_data()
        
        # Atualiza cache
        update_cache(data)
        
        print("✅ Dados processados e servidos com sucesso")
        return jsonify(data)
    
    except Exception as e:
        error_message = str(e)
        print(f"❌ Erro no endpoint /api/chamados: {error_message}")
        
        # Retorna dados do cache se disponível, mesmo que expirado
        if cache['data'] is not None:
            print("⚠️ Retornando dados do cache (podem estar desatualizados)")
            cache_data = cache['data'].copy()
            cache_data['warning'] = 'Dados podem estar desatualizados devido a erro na atualização'
            return jsonify(cache_data)
        
        # Se não há cache, retorna erro claro (sem modo demonstração)
        return jsonify({
            'error': True,
            'message': 'Falha ao obter dados dos chamados',
            'details': error_message,
            'hint': 'Verifique o ID do arquivo no Google Drive, permissões de compartilhamento com o e-mail do service account e o caminho para as credenciais.'
        }), 500


@app.route('/api/chamados/refresh', methods=['POST'])
def refresh_chamados():
    """
    Endpoint para forçar atualização dos dados
    Limpa o cache e busca dados atualizados
    """
    try:
        print("🔄 Forçando atualização dos dados...")
        
        # Limpa cache
        cache['data'] = None
        cache['timestamp'] = None
        
        # Busca dados atualizados
        sheets_client = create_google_sheets_client()
        data = sheets_client.process_chamados_data()
        
        # Atualiza cache
        update_cache(data)
        
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso',
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao atualizar dados',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/config')
def get_config():
    """Endpoint para retornar configurações públicas da aplicação"""
    return jsonify({
        'sheets_id': os.getenv('GOOGLE_SHEETS_ID', 'não configurado'),
        'cache_timeout': cache['timeout'],
        'environment': os.getenv('FLASK_ENV', 'production'),
        'cors_origins': cors_origins
    })


@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    return jsonify({
        'error': True,
        'message': 'Endpoint não encontrado',
        'available_endpoints': [
            'GET /',
            'GET /api/health',
            'GET /api/chamados',
            'POST /api/chamados/refresh',
            'GET /api/config'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos do servidor"""
    return jsonify({
        'error': True,
        'message': 'Erro interno do servidor',
        'details': str(error)
    }), 500


if __name__ == '__main__':
    # Configurações do servidor
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print("🚀 Iniciando TechHelp Dashboard API...")
    print(f"📊 Google Sheets ID: {os.getenv('GOOGLE_SHEETS_ID', 'não configurado')}")
    print(f"🌐 Porta: {port}")
    print(f"🔧 Debug: {debug_mode}")
    print(f"⏱️ Cache timeout: {cache['timeout']}s")
    
    # Inicia o servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )