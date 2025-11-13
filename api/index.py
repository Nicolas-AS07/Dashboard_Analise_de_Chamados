"""
TechHelp Dashboard API - Versão Serverless MÍNIMA
Criado especificamente para Vercel - SEM dependências pesadas
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# Cria app Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Cache global
_cache = {'data': None, 'timestamp': None}


@app.route('/')
def home():
    return jsonify({
        'name': 'TechHelp Dashboard API',
        'version': '2.0-serverless',
        'status': 'online',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/test')
def test():
    """Diagnóstico completo"""
    result = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Teste 1: Variáveis de ambiente
    has_url = bool(os.getenv('SUPABASE_URL'))
    has_key = bool(os.getenv('SUPABASE_KEY'))
    result['tests']['env_vars'] = {
        'url': '✅' if has_url else '❌',
        'key': '✅' if has_key else '❌'
    }
    
    if not has_url or not has_key:
        result['error'] = 'FALTAM VARIÁVEIS DE AMBIENTE'
        return jsonify(result), 500
    
    # Teste 2: Import Supabase
    try:
        from supabase import create_client
        result['tests']['import_supabase'] = '✅'
    except Exception as e:
        result['tests']['import_supabase'] = f'❌ {str(e)}'
        result['error'] = 'FALHA AO IMPORTAR SUPABASE'
        return jsonify(result), 500
    
    # Teste 3: Criar cliente
    try:
        client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
        result['tests']['create_client'] = '✅'
    except Exception as e:
        result['tests']['create_client'] = f'❌ {str(e)}'
        result['error'] = 'FALHA AO CRIAR CLIENTE'
        return jsonify(result), 500
    
    # Teste 4: Query
    try:
        response = client.table('chamados').select('*').limit(1).execute()
        result['tests']['query'] = f"✅ {len(response.data)} registros"
    except Exception as e:
        result['tests']['query'] = f'❌ {str(e)}'
        result['error'] = 'FALHA NA QUERY'
        return jsonify(result), 500
    
    result['status'] = '✅ TODOS TESTES PASSARAM'
    return jsonify(result), 200


@app.route('/api/chamados')
def get_chamados():
    """Endpoint principal - versão simplificada"""
    try:
        # Verifica variáveis
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            return jsonify({
                'error': True,
                'message': 'Variáveis de ambiente não configuradas',
                'hint': 'Configure SUPABASE_URL e SUPABASE_KEY na Vercel'
            }), 500
        
        # Verifica cache (5 minutos)
        if _cache['data'] and _cache['timestamp']:
            age = (datetime.now() - _cache['timestamp']).seconds
            if age < 300:
                return jsonify(_cache['data'])
        
        # Importa e conecta
        from supabase import create_client
        client = create_client(url, key)
        
        # Busca dados
        response = client.table('chamados').select('*').execute()
        data = response.data
        
        # Processa com Python puro (SEM pandas)
        total = len(data)
        
        # Conta status
        status_count = {}
        for row in data:
            s = str(row.get('status', 'desconhecido')).lower()
            status_count[s] = status_count.get(s, 0) + 1
        
        abertos = sum(status_count.get(k, 0) for k in ['aberto', 'em andamento', 'pendente'])
        fechados = sum(status_count.get(k, 0) for k in ['fechado', 'resolvido', 'concluído', 'concluido'])
        
        # Conta técnicos
        tecnico_count = {}
        for row in data:
            t = row.get('tecnico', 'N/A')
            tecnico_count[t] = tecnico_count.get(t, 0) + 1
        
        # Conta categorias
        cat_count = {}
        for row in data:
            c = row.get('categoria', 'N/A')
            cat_count[c] = cat_count.get(c, 0) + 1
        
        # Monta resultado
        result = {
            'total_chamados': total,
            'total_abertos': abertos,
            'total_fechados': fechados,
            'tempo_medio_resolucao': 'N/A',
            'chamados_por_tecnico': tecnico_count,
            'categorias': cat_count,
            'tabela': data[:100],
            'insights': {
                'melhor_tecnico': max(tecnico_count.items(), key=lambda x: x[1])[0] if tecnico_count else 'N/A',
                'categoria_predominante': max(cat_count.items(), key=lambda x: x[1])[0] if cat_count else 'N/A',
                'tendencia_satisfacao': 'Processando...'
            },
            'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fonte': 'Supabase'
        }
        
        # Atualiza cache
        _cache['data'] = result
        _cache['timestamp'] = datetime.now()
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': True,
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500


# Handler para Vercel
def handler(request):
    return app(request.environ, lambda *args: None)
