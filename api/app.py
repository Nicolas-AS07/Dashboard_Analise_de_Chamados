"""
TechHelp Dashboard - API Flask
Servidor backend para integração com Google Sheets e fornecimento de dados para o dashboard
"""
import os
import sys
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Adiciona o diretório api ao path para imports funcionarem na Vercel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from supabase_client import create_supabase_client
except ImportError as e:
    print(f"❌ Erro ao importar supabase_client: {e}")
    # Fallback: tenta importar diretamente
    import supabase_client
    create_supabase_client = supabase_client.create_supabase_client


# Carrega variáveis de ambiente (produção usa variáveis da Vercel, desenvolvimento usa .env)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'config', '.env'))

# Diagnóstico inicial
print(f"🔍 Diagnóstico do ambiente:")
print(f"  - Python: {sys.version}")
print(f"  - BASE_DIR: {BASE_DIR}")
print(f"  - ENV_PATH: {ENV_PATH}")
print(f"  - ENV_PATH existe: {os.path.exists(ENV_PATH)}")

# Só tenta carregar .env se o arquivo existir (desenvolvimento local)
if os.path.exists(ENV_PATH):
    print(f"🔧 Carregando .env de: {ENV_PATH}")
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    print(f"📦 Ambiente de produção - usando variáveis de ambiente do sistema")

# Verifica variáveis críticas (sem expor valores)
print(f"🔑 Variáveis de ambiente:")
print(f"  - SUPABASE_URL: {'✅' if os.getenv('SUPABASE_URL') else '❌'}")
print(f"  - SUPABASE_KEY: {'✅' if os.getenv('SUPABASE_KEY') else '❌'}")
print(f"  - DATA_SOURCE: {os.getenv('DATA_SOURCE', 'não definido')}")
print(f"  - FLASK_ENV: {os.getenv('FLASK_ENV', 'não definido')}")

# Configuração da aplicação Flask
app = Flask(__name__)

# Configuração CORS para permitir requisições do frontend
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins, resources={r"/api/*": {"origins": "*"}})

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
        'version': '2.0.0',
        'status': 'online',
        'endpoints': [
            'GET /api/test - Teste de diagnóstico completo',
            'GET /api/chamados - Retorna dados dos chamados',
            'GET /api/health - Verifica status da API'
        ],
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/test')
def test_supabase():
    """
    Endpoint de teste para diagnosticar problemas de conexão e imports
    """
    diagnostics = {
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'SUPABASE_URL': os.getenv('SUPABASE_URL', 'NOT SET')[:50] + '...' if os.getenv('SUPABASE_URL') else 'NOT SET',
            'SUPABASE_KEY_LENGTH': len(os.getenv('SUPABASE_KEY', '')) if os.getenv('SUPABASE_KEY') else 0,
            'DATA_SOURCE': os.getenv('DATA_SOURCE', 'NOT SET'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'NOT SET'),
            'PYTHON_VERSION': sys.version.split()[0]
        },
        'tests': {}
    }
    
    try:
        # Teste 1: Variáveis de ambiente
        has_url = bool(os.getenv('SUPABASE_URL'))
        has_key = bool(os.getenv('SUPABASE_KEY'))
        diagnostics['tests']['1_env_vars'] = {
            'status': 'PASS' if (has_url and has_key) else 'FAIL',
            'message': f"URL: {'✅' if has_url else '❌'}, KEY: {'✅' if has_key else '❌'}"
        }
        
        if not has_url or not has_key:
            diagnostics['overall'] = 'FAIL: Variáveis de ambiente não configuradas'
            return jsonify(diagnostics), 500
        
        # Teste 2: Import supabase
        try:
            from supabase import create_client as supabase_create_client
            diagnostics['tests']['2_import_supabase'] = {
                'status': 'PASS',
                'message': 'Módulo supabase OK'
            }
        except Exception as e:
            diagnostics['tests']['2_import_supabase'] = {
                'status': 'FAIL',
                'message': str(e)
            }
            diagnostics['overall'] = 'FAIL: Não foi possível importar supabase'
            return jsonify(diagnostics), 500
        
        # Teste 3: Criar cliente
        try:
            client = supabase_create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
            diagnostics['tests']['3_create_client'] = {
                'status': 'PASS',
                'message': 'Cliente criado'
            }
        except Exception as e:
            diagnostics['tests']['3_create_client'] = {
                'status': 'FAIL',
                'message': str(e)
            }
            diagnostics['overall'] = 'FAIL: Erro ao criar cliente Supabase'
            return jsonify(diagnostics), 500
        
        # Teste 4: Query na tabela
        try:
            response = client.table('chamados').select('*').limit(1).execute()
            has_data = len(response.data) > 0
            diagnostics['tests']['4_query_table'] = {
                'status': 'PASS',
                'message': f"{'Dados encontrados' if has_data else 'Tabela vazia'}",
                'rows': len(response.data),
                'columns': list(response.data[0].keys()) if has_data else []
            }
        except Exception as e:
            diagnostics['tests']['4_query_table'] = {
                'status': 'FAIL',
                'message': str(e)
            }
            import traceback
            diagnostics['tests']['4_query_table']['trace'] = traceback.format_exc()[-500:]
            diagnostics['overall'] = 'FAIL: Erro ao consultar tabela chamados'
            return jsonify(diagnostics), 500
        
        # Teste 5: Import pandas/numpy
        try:
            import pandas as pd
            import numpy as np
            diagnostics['tests']['5_data_libs'] = {
                'status': 'PASS',
                'message': f"pandas {pd.__version__}, numpy {np.__version__}"
            }
        except Exception as e:
            diagnostics['tests']['5_data_libs'] = {
                'status': 'FAIL',
                'message': str(e)
            }
            diagnostics['overall'] = 'FAIL: Erro ao importar pandas/numpy'
            return jsonify(diagnostics), 500
        
        diagnostics['overall'] = '✅ TODOS OS TESTES PASSARAM'
        return jsonify(diagnostics), 200
        
    except Exception as e:
        diagnostics['overall'] = f'❌ ERRO CRÍTICO: {str(e)}'
        import traceback
        diagnostics['traceback'] = traceback.format_exc()
        return jsonify(diagnostics), 500


@app.route('/api/health')
def health_check():
    """Endpoint de verificação de saúde da API"""
    try:
        # Testa conexão com Supabase
        supabase_client = create_supabase_client()
        
        return jsonify({
            'status': 'healthy',
            'supabase': 'connected',
            'cache_valid': is_cache_valid(),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'supabase': 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/chamados')
def get_chamados():
    """
    Endpoint principal que retorna dados processados dos chamados
    Utiliza cache para otimizar performance
    """
    print(f"\n{'='*60}")
    print(f"🔵 Requisição /api/chamados iniciada")
    print(f"{'='*60}")
    
    try:
        # Verifica variáveis de ambiente críticas
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        print(f"🔍 Verificando variáveis de ambiente...")
        print(f"  SUPABASE_URL: {'✅ SET' if supabase_url else '❌ NOT SET'}")
        print(f"  SUPABASE_KEY: {'✅ SET' if supabase_key else '❌ NOT SET'}")
        
        if not supabase_url or not supabase_key:
            error_msg = f"Variáveis de ambiente faltando - URL: {bool(supabase_url)}, KEY: {bool(supabase_key)}"
            print(f"❌ {error_msg}")
            return jsonify({
                'error': True,
                'message': 'Configuração incompleta',
                'details': error_msg,
                'hint': 'Configure SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente da Vercel'
            }), 500
        
        # Verifica se pode usar cache
        if is_cache_valid():
            print("📋 Dados servidos do cache")
            return jsonify(cache['data'])
        
        print("🔄 Buscando dados do Supabase...")
        
        # MODO SIMPLIFICADO: Conecta direto sem usar supabase_client.py
        try:
            from supabase import create_client as supabase_create_client
            print("✅ Módulo supabase importado")
            
            client = supabase_create_client(supabase_url, supabase_key)
            print("✅ Cliente Supabase criado")
            
            # Query simples
            response = client.table('chamados').select('*').execute()
            print(f"✅ Query executada: {len(response.data)} registros")
            
            # Processamento MÍNIMO - apenas contar dados
            total = len(response.data)
            
            # Conta status (simples, sem pandas)
            status_counts = {}
            for row in response.data:
                status = str(row.get('status', 'desconhecido')).lower()
                status_counts[status] = status_counts.get(status, 0) + 1
            
            abertos = status_counts.get('aberto', 0) + status_counts.get('em andamento', 0) + status_counts.get('pendente', 0)
            fechados = status_counts.get('fechado', 0) + status_counts.get('resolvido', 0) + status_counts.get('concluído', 0)
            
            # Conta técnicos (simples)
            tecnico_counts = {}
            for row in response.data:
                tecnico = row.get('tecnico', 'N/A')
                tecnico_counts[tecnico] = tecnico_counts.get(tecnico, 0) + 1
            
            # Conta categorias (simples)
            categoria_counts = {}
            for row in response.data:
                categoria = row.get('categoria', 'N/A')
                categoria_counts[categoria] = categoria_counts.get(categoria, 0) + 1
            
            # Monta resposta simples
            data = {
                'total_chamados': total,
                'total_abertos': abertos,
                'total_fechados': fechados,
                'tempo_medio_resolucao': 'N/A',
                'chamados_por_tecnico': tecnico_counts,
                'categorias': categoria_counts,
                'tabela': response.data[:50],  # Primeiros 50
                'insights': {
                    'melhor_tecnico': f"🏆 {max(tecnico_counts.items(), key=lambda x: x[1])[0] if tecnico_counts else 'N/A'}",
                    'categoria_predominante': f"📊 {max(categoria_counts.items(), key=lambda x: x[1])[0] if categoria_counts else 'N/A'}",
                    'tendencia_satisfacao': 'Dados sendo processados...'
                },
                'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'fonte': 'Supabase (modo simplificado)',
                'debug_mode': True
            }
            
            # Atualiza cache
            update_cache(data)
            
            print("✅ Dados processados e retornados com sucesso")
            print(f"{'='*60}\n")
            return jsonify(data)
            
        except Exception as e:
            print(f"❌ Erro no modo simplificado: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
        return jsonify(data)
    
    except Exception as e:
        error_message = str(e)
        print(f"❌ Erro no endpoint /api/chamados: {error_message}")
        import traceback
        error_traceback = traceback.format_exc()
        print(error_traceback)
        
        # Retorna dados do cache se disponível, mesmo que expirado
        if cache['data'] is not None:
            print("⚠️ Retornando dados do cache (podem estar desatualizados)")
            cache_data = cache['data'].copy()
            cache_data['warning'] = 'Dados podem estar desatualizados devido a erro na atualização'
            return jsonify(cache_data)
        
        # Se não há cache, retorna erro detalhado
        return jsonify({
            'error': True,
            'message': 'Falha ao obter dados dos chamados',
            'details': error_message,
            'traceback': error_traceback if os.getenv('FLASK_ENV') == 'development' else 'Veja os logs da função',
            'environment': {
                'SUPABASE_URL': bool(os.getenv('SUPABASE_URL')),
                'SUPABASE_KEY': bool(os.getenv('SUPABASE_KEY')),
                'DATA_SOURCE': os.getenv('DATA_SOURCE')
            }
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
        supabase_client = create_supabase_client()
        data = supabase_client.process_chamados_data()
        
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
        'supabase_url': os.getenv('SUPABASE_URL', 'não configurado')[:30] + '...' if os.getenv('SUPABASE_URL') else 'não configurado',
        'cache_timeout': cache['timeout'],
        'environment': os.getenv('FLASK_ENV', 'production'),
        'cors_origins': cors_origins,
        'data_source': 'Supabase'
    })


@app.route('/api/diagnostics')
def diagnostics():
    """Endpoint de diagnóstico detalhado da integração com Supabase."""
    try:
        supabase_client = create_supabase_client()
        diag = supabase_client.get_diagnostics()

        # Dica se falhar na conexão
        hint = None
        if not diag.get('connected'):
            hint = diag.get('hint', 'Verifique SUPABASE_URL e SUPABASE_KEY no .env')

        return jsonify({
            'status': 'ok' if diag.get('connected') and diag.get('table_exists') else 'partial',
            'env': {
                'supabase_url_set': os.getenv('SUPABASE_URL') is not None,
                'supabase_key_set': os.getenv('SUPABASE_KEY') is not None,
            },
            'diagnostics': diag,
            'hint': hint
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Falha ao obter diagnósticos',
            'error': str(e)
        }), 500


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
    print(f"📊 Fonte de dados: Supabase")
    print(f"🔗 Supabase URL: {os.getenv('SUPABASE_URL', 'não configurado')[:40]}...")
    print(f"🌐 Porta: {port}")
    print(f"🔧 Debug: {debug_mode}")
    print(f"⏱️ Cache timeout: {cache['timeout']}s")
    
    # Inicia o servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )