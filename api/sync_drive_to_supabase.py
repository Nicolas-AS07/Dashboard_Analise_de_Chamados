"""
Script de sincronização Drive → Supabase
Responsável por:
 - Ler Excel/Google Sheets do Google Drive
 - Normalizar dados (colunas, tipos, satisfação textual→numérica)
 - Inserir/atualizar registros no Supabase (tabela chamados)
 
Uso:
 - Executar manualmente: python sync_drive_to_supabase.py
 - Agendar via cron/Task Scheduler para sync automático
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from google_sheets import GoogleSheetsIntegration
from supabase_client import create_supabase_client
import pandas as pd
import unicodedata
import re


# Carrega variáveis de ambiente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'config', '.env'))
load_dotenv(dotenv_path=ENV_PATH, override=True)


def normalize_column_name(text: str) -> str:
    """Normaliza nomes de colunas para padrão do banco"""
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize('NFKD', text)
    no_accents = ''.join([c for c in nfkd if not unicodedata.category(c) == 'Mn'])
    base = no_accents.strip().lower().replace('ç', 'c')
    cleaned = re.sub(r'[^a-z0-9]+', '_', base)
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapeia colunas da planilha para padrão do banco"""
    # Normaliza nomes
    df.columns = [normalize_column_name(col) for col in df.columns]
    
    # Mapeamento de variações para nomes padrão
    column_mapping = {
        'id_chamado': ['id_chamado', 'id', 'chamado_id', 'numero', 'id_do_chamado'],
        'data_abertura': ['data_abertura', 'abertura', 'data_inicio', 'data_de_abertura'],
        'data_fechamento': ['data_fechamento', 'fechamento', 'data_fim', 'data_de_fechamento'],
        'tecnico': ['tecnico', 'responsavel', 'atendente', 'agente_responsavel'],
        'categoria': ['categoria', 'tipo', 'classificacao', 'motivo'],
        'status': ['status', 'situacao', 'estado'],
        'tempo_resolucao': ['tempo_resolucao', 'tempo', 'duracao', 'tma_minutos'],
        'satisfacao': ['satisfacao', 'nota', 'avaliacao', 'satisfacao_do_cliente'],
        'solicitante': ['solicitante', 'cliente', 'usuario'],
        'departamento': ['departamento', 'area', 'setor'],
        'prioridade': ['prioridade', 'urgencia'],
        'solucao': ['solucao', 'resolucao', 'descricao_solucao']
    }
    
    # Renomeia
    for standard, variations in column_mapping.items():
        for var in variations:
            if var in df.columns:
                df = df.rename(columns={var: standard})
                break
    
    return df


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Converte tipos de dados"""
    # Datas
    date_cols = ['data_abertura', 'data_fechamento']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Satisfação textual → numérica
    if 'satisfacao' in df.columns:
        satisf_map = {
            'ruim': 1, 'regular': 2, 'medio': 3, 'médio': 3,
            'bom': 4, 'otimo': 5, 'ótimo': 5, 'excelente': 5
        }
        df['satisfacao'] = df['satisfacao'].apply(
            lambda x: satisf_map.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )
        df['satisfacao'] = pd.to_numeric(df['satisfacao'], errors='coerce')
    
    # Tempo de resolução: se vier em minutos (TMA), converte para horas
    if 'tempo_resolucao' in df.columns:
        df['tempo_resolucao'] = pd.to_numeric(df['tempo_resolucao'], errors='coerce')
        # Se valores muito altos, provavelmente são minutos
        if df['tempo_resolucao'].median() > 100:
            print("⚠️ Convertendo tempo_resolucao de minutos para horas")
            df['tempo_resolucao'] = df['tempo_resolucao'] / 60.0
    
    return df


def sync_to_supabase(df: pd.DataFrame, supabase_client):
    """Sincroniza DataFrame com Supabase (upsert)"""
    print(f"📤 Sincronizando {len(df)} registros para o Supabase...")
    
    # Converte para lista de dicts
    records = df.to_dict('records')
    
    # Limpa valores NaN/None para evitar erros no Supabase
    for record in records:
        for key, value in list(record.items()):
            if pd.isna(value):
                record[key] = None
            # Converte timestamps para string ISO
            elif isinstance(value, pd.Timestamp):
                record[key] = value.isoformat() if pd.notna(value) else None
    
    try:
        # Upsert por lote (Supabase permite inserção em massa)
        # Se id_chamado existir, atualiza; senão, insere
        response = supabase_client.client.table('chamados').upsert(
            records,
            on_conflict='id_chamado'
        ).execute()
        
        print(f"✅ Sincronização concluída: {len(response.data)} registros processados")
        return True
        
    except Exception as e:
        print(f"❌ Erro na sincronização: {str(e)}")
        return False


def main():
    """Função principal de sincronização"""
    print("=" * 60)
    print("🔄 SYNC DRIVE → SUPABASE")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    try:
        # 1. Conecta ao Google Drive/Sheets
        print("📊 Lendo dados do Google Drive...")
        sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'config/service-account.json')
        
        if not sheets_id:
            raise Exception("GOOGLE_SHEETS_ID não configurado no .env")
        
        google_client = GoogleSheetsIntegration(sheets_id, credentials_path)
        df = google_client.get_spreadsheet_data()
        print(f"✅ Lidos {len(df)} registros do Drive\n")
        
        # 2. Normaliza e mapeia colunas
        print("🔧 Normalizando dados...")
        df = map_columns(df)
        df = convert_data_types(df)
        print(f"✅ Colunas mapeadas: {', '.join(df.columns)}\n")
        
        # 3. Conecta ao Supabase
        print("🔗 Conectando ao Supabase...")
        supabase_client = create_supabase_client()
        print("✅ Conexão estabelecida\n")
        
        # 4. Sincroniza dados
        success = sync_to_supabase(df, supabase_client)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("❌ SINCRONIZAÇÃO FALHOU")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
