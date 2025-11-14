"""
TechHelp Dashboard API - Versão Serverless para Vercel
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Cache simples
_cache = {'data': None, 'ts': None}


@app.route('/')
@app.route('/api')
def home():
    return jsonify({
        'name': 'TechHelp Dashboard API',
        'version': '2.0',
        'status': 'online',
        'endpoints': ['/api/health', '/api/test', '/api/chamados']
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})


@app.route('/api/test')
def test():
    """Diagnóstico"""
    result = {'tests': {}, 'timestamp': datetime.now().isoformat()}
    
    # Teste variáveis
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    result['tests']['env'] = {
        'url': '✅' if url else '❌',
        'key': '✅' if key else '❌'
    }
    
    if not url or not key:
        result['error'] = 'Variáveis de ambiente não configuradas'
        return jsonify(result), 500
    
    # Teste import
    try:
        from supabase import create_client
        result['tests']['import'] = '✅'
    except Exception as e:
        result['tests']['import'] = f'❌ {e}'
        return jsonify(result), 500
    
    # Teste conexão
    try:
        client = create_client(url, key)
        result['tests']['client'] = '✅'
    except Exception as e:
        result['tests']['client'] = f'❌ {e}'
        return jsonify(result), 500
    
    # Teste query
    try:
        res = client.table('chamados').select('*').limit(1).execute()
        result['tests']['query'] = f'✅ {len(res.data)} rows'
        result['sample'] = res.data[0] if res.data else None
    except Exception as e:
        result['tests']['query'] = f'❌ {e}'
        return jsonify(result), 500
    
    result['status'] = 'ALL PASS'
    return jsonify(result)


@app.route('/api/chamados')
def get_chamados():
    """Dados dos chamados"""
    try:
        # Verifica env
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            return jsonify({
                'error': True,
                'message': 'Variáveis não configuradas'
            }), 500
        
        # Cache (5min)
        now = datetime.now()
        if _cache['data'] and _cache['ts']:
            if (now - _cache['ts']).seconds < 300:
                return jsonify(_cache['data'])
        
        # Busca dados
        from supabase import create_client
        client = create_client(url, key)
        response = client.table('chamados').select('*').execute()
        data = response.data
        
        if not data:
            return jsonify({
                'error': True,
                'message': 'Nenhum dado encontrado na tabela'
            }), 404
        
        # Processa
        total = len(data)
        
        # Status
        status = {}
        for r in data:
            s = str(r.get('status', '')).lower().strip()
            status[s] = status.get(s, 0) + 1
        
        abertos = sum(status.get(k, 0) for k in ['aberto', 'em andamento', 'pendente'])
        fechados = sum(status.get(k, 0) for k in ['fechado', 'resolvido', 'concluído', 'concluido'])
        
        # Técnicos
        tecnicos = {}
        for r in data:
            t = r.get('tecnico') or 'N/A'
            tecnicos[t] = tecnicos.get(t, 0) + 1
        
        # Categorias
        cats = {}
        for r in data:
            c = r.get('categoria') or 'N/A'
            cats[c] = cats.get(c, 0) + 1
        
        # Resultado
        result = {
            'total_chamados': total,
            'total_abertos': abertos,
            'total_fechados': fechados,
            'tempo_medio_resolucao': 'N/A',
            'chamados_por_tecnico': tecnicos,
            'categorias': cats,
            'tabela': data[:100],
            'insights': {
                'melhor_tecnico': max(tecnicos.items(), key=lambda x: x[1])[0] if tecnicos else 'N/A',
                'categoria_predominante': max(cats.items(), key=lambda x: x[1])[0] if cats else 'N/A',
                'tendencia_satisfacao': 'OK'
            },
            'ultima_atualizacao': now.strftime('%d/%m/%Y %H:%M'),
            'fonte': 'Supabase'
        }
        
        # Cache
        _cache['data'] = result
        _cache['ts'] = now
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': True,
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500
