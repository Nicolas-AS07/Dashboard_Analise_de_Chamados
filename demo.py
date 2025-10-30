"""
Demonstração do TechHelp Dashboard
Teste simples das funcionalidades principais
"""
import json
from datetime import datetime


def create_demo_data():
    """Cria dados de demonstração para o dashboard"""
    return {
        "total_chamados": 67,
        "total_abertos": 18,
        "total_fechados": 49,
        "tempo_medio_resolucao": "2.8 horas",
        "chamados_por_tecnico": {
            "João Silva": 16,
            "Maria Santos": 14,
            "Carlos Oliveira": 12,
            "Ana Costa": 11,
            "Pedro Ferreira": 8,
            "Luciana Rocha": 6
        },
        "categorias": {
            "Hardware": 22,
            "Software": 18,
            "Rede": 12,
            "Sistema": 9,
            "Usuario": 6
        },
        "tabela": [
            {"id": "TH001", "tecnico": "João Silva", "categoria": "Hardware", "status": "Fechado", "satisfacao": 5},
            {"id": "TH002", "tecnico": "Maria Santos", "categoria": "Software", "status": "Aberto", "satisfacao": "N/A"},
            {"id": "TH003", "tecnico": "Carlos Oliveira", "categoria": "Rede", "status": "Fechado", "satisfacao": 4},
            {"id": "TH004", "tecnico": "Ana Costa", "categoria": "Sistema", "status": "Em Andamento", "satisfacao": "N/A"},
            {"id": "TH005", "tecnico": "Pedro Ferreira", "categoria": "Usuario", "status": "Fechado", "satisfacao": 5},
            {"id": "TH006", "tecnico": "Luciana Rocha", "categoria": "Hardware", "status": "Fechado", "satisfacao": 3},
            {"id": "TH007", "tecnico": "João Silva", "categoria": "Software", "status": "Aberto", "satisfacao": "N/A"},
            {"id": "TH008", "tecnico": "Maria Santos", "categoria": "Rede", "status": "Fechado", "satisfacao": 4},
            {"id": "TH009", "tecnico": "Carlos Oliveira", "categoria": "Sistema", "status": "Fechado", "satisfacao": 5},
            {"id": "TH010", "tecnico": "Ana Costa", "categoria": "Hardware", "status": "Em Andamento", "satisfacao": "N/A"}
        ],
        "insights": {
            "melhor_tecnico": "🏆 João Silva foi o técnico mais produtivo com 16 chamados resolvidos.",
            "categoria_predominante": "📈 Hardware representa 32.8% dos chamados (22 ocorrências).",
            "tendencia_satisfacao": "😊 Excelente! Satisfação média de 4.3/5 - clientes muito satisfeitos."
        },
        "ultima_atualizacao": datetime.now().strftime('%d/%m/%Y %H:%M')
    }


def validate_data_structure(data):
    """Valida a estrutura dos dados"""
    required_fields = [
        'total_chamados', 'total_abertos', 'total_fechados',
        'tempo_medio_resolucao', 'chamados_por_tecnico',
        'categorias', 'tabela', 'insights', 'ultima_atualizacao'
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Campos obrigatórios faltando: {', '.join(missing_fields)}")
        return False
    
    print("✅ Estrutura de dados válida")
    return True


def export_demo_data():
    """Exporta dados de demonstração para arquivo JSON"""
    data = create_demo_data()
    
    with open('demo_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("📄 Dados de demonstração exportados para demo_data.json")
    return data


def main():
    """Função principal de demonstração"""
    print("🧪 === DEMONSTRAÇÃO TECHHELP DASHBOARD ===")
    print()
    
    # Cria dados de demonstração
    print("📊 Criando dados de demonstração...")
    data = create_demo_data()
    
    # Valida estrutura
    print("🔍 Validando estrutura dos dados...")
    is_valid = validate_data_structure(data)
    
    if not is_valid:
        print("❌ Falha na validação")
        return
    
    # Exibe resumo
    print()
    print("📈 === RESUMO DOS DADOS ===")
    print(f"Total de Chamados: {data['total_chamados']}")
    print(f"Chamados Abertos: {data['total_abertos']}")
    print(f"Chamados Fechados: {data['total_fechados']}")
    print(f"Tempo Médio: {data['tempo_medio_resolucao']}")
    print()
    
    print("👥 Top 3 Técnicos:")
    sorted_technicians = sorted(data['chamados_por_tecnico'].items(), key=lambda x: x[1], reverse=True)
    for i, (name, count) in enumerate(sorted_technicians[:3], 1):
        print(f"  {i}. {name}: {count} chamados")
    print()
    
    print("📂 Top 3 Categorias:")
    sorted_categories = sorted(data['categorias'].items(), key=lambda x: x[1], reverse=True)
    for i, (category, count) in enumerate(sorted_categories[:3], 1):
        percentage = (count / data['total_chamados']) * 100
        print(f"  {i}. {category}: {count} chamados ({percentage:.1f}%)")
    print()
    
    print("💡 Insights:")
    for key, insight in data['insights'].items():
        print(f"  • {insight}")
    print()
    
    # Exporta dados
    export_demo_data()
    
    print("✅ Demonstração concluída com sucesso!")
    print()
    print("🚀 Para executar o dashboard completo:")
    print("1. Configure as credenciais do Google (config/service-account.json)")
    print("2. Execute: cd api && python app.py")
    print("3. Execute: cd frontend && python -m http.server 8080")
    print("4. Acesse: http://localhost:8080")


if __name__ == "__main__":
    main()