"""
Integração com Supabase para TechHelp Dashboard
Responsável por:
 - Conectar ao Supabase e ler dados da tabela chamados
 - Processar dados e calcular métricas (KPIs, gráficos, insights)
 - Fornecer interface consistente para a API Flask
"""
import os
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from supabase import create_client, Client


class SupabaseIntegration:
    """Classe para integração com Supabase"""
    
    def __init__(self, url: str, key: str):
        """
        Inicializa a integração com Supabase
        
        Args:
            url: URL do projeto Supabase
            key: API Key (anon key para leitura pública ou service_role para admin)
        """
        self.url = url
        self.key = key
        self.client: Client = None
        self._connect()
    
    def _connect(self):
        """Conecta ao Supabase"""
        try:
            self.client = create_client(self.url, self.key)
            print("✅ Conexão com Supabase estabelecida")
        except Exception as e:
            print(f"❌ Erro ao conectar ao Supabase: {str(e)}")
            raise
    
    def get_chamados_data(self) -> pd.DataFrame:
        """
        Busca dados da tabela chamados no Supabase
        
        Returns:
            DataFrame com os dados dos chamados
        """
        try:
            # Query na tabela chamados (ajuste o nome se necessário)
            response = self.client.table('chamados').select('*').execute()
            
            if not response.data:
                raise Exception("Nenhum dado encontrado na tabela chamados")
            
            # Converte para DataFrame
            df = pd.DataFrame(response.data)
            
            print(f"✅ Dados do Supabase carregados: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao buscar dados do Supabase: {str(e)}")
            raise
    
    def process_chamados_data(self) -> Dict[str, Any]:
        """
        Processa os dados e retorna métricas calculadas
        
        Returns:
            Dicionário com KPIs e dados processados
        """
        try:
            # Carrega dados do Supabase
            df = self.get_chamados_data()
            
            # Normaliza nomes das colunas (caso venham diferentes)
            df.columns = [col.lower().strip() for col in df.columns]
            
            # Converte tipos de dados
            df = self._convert_data_types(df)
            
            # Calcula métricas
            metrics = self._calculate_metrics(df)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erro no processamento: {str(e)}")
            raise
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas para tipos de dados apropriados"""
        try:
            # Converte datas
            date_columns = ['data_abertura', 'data_fechamento', 'created_at', 'updated_at']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Converte satisfação para numérico
            if 'satisfacao' in df.columns:
                # Mapeia textuais para numéricos
                satisf_map = {
                    'ruim': 1, 'regular': 2, 'medio': 3, 'médio': 3,
                    'bom': 4, 'otimo': 5, 'ótimo': 5, 'excelente': 5
                }
                df['satisfacao'] = df['satisfacao'].apply(
                    lambda x: satisf_map.get(str(x).strip().lower(), x) if pd.notna(x) else x
                )
                df['satisfacao'] = pd.to_numeric(df['satisfacao'], errors='coerce')
            
            # Converte tempo de resolução para numérico (em horas)
            if 'tempo_resolucao' in df.columns:
                df['tempo_resolucao'] = pd.to_numeric(df['tempo_resolucao'], errors='coerce')
            
            return df
            
        except Exception as e:
            print(f"⚠️ Aviso na conversão de tipos: {str(e)}")
            return df
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula KPIs e métricas do dashboard"""
        try:
            # KPIs básicos
            total_chamados = len(df)
            
            # Filtra por status
            if 'status' in df.columns:
                df['status'] = df['status'].astype(str).str.lower().str.strip()
                total_abertos = len(df[df['status'].isin(['aberto', 'em andamento', 'pendente'])])
                total_fechados = len(df[df['status'].isin(['fechado', 'resolvido', 'concluido', 'concluído'])])
            else:
                total_abertos = 0
                total_fechados = total_chamados
            
            # Tempo médio de resolução
            tempo_medio = "N/A"
            if 'tempo_resolucao' in df.columns:
                tempo_medio_num = df['tempo_resolucao'].mean()
                if not pd.isna(tempo_medio_num):
                    tempo_medio = f"{tempo_medio_num:.1f} horas"
            elif 'data_abertura' in df.columns and 'data_fechamento' in df.columns:
                # Calcula a partir das datas
                diffs = (df['data_fechamento'] - df['data_abertura']).dt.total_seconds() / 3600.0
                tempo_medio_num = diffs.dropna().mean()
                if pd.notna(tempo_medio_num):
                    tempo_medio = f"{tempo_medio_num:.1f} horas"
            
            # Chamados por técnico
            chamados_por_tecnico = {}
            if 'tecnico' in df.columns:
                tecnico_counts = df['tecnico'].value_counts()
                chamados_por_tecnico = tecnico_counts.to_dict()
            
            # Categorias mais recorrentes
            categorias = {}
            if 'categoria' in df.columns:
                categoria_counts = df['categoria'].value_counts()
                categorias = categoria_counts.to_dict()
            
            # Dados para tabela (limita a 100 registros mais recentes)
            tabela_dados = []
            df_sorted = df.sort_values('data_abertura', ascending=False) if 'data_abertura' in df.columns else df
            
            for _, row in df_sorted.head(100).iterrows():
                tabela_dados.append({
                    'id': row.get('id_chamado', row.get('id', 'N/A')),
                    'tecnico': row.get('tecnico', 'N/A'),
                    'categoria': row.get('categoria', 'N/A'),
                    'status': row.get('status', 'N/A'),
                    'satisfacao': row.get('satisfacao', 'N/A')
                })
            
            # Gera insights automáticos
            insights = self._generate_insights(df, chamados_por_tecnico, categorias)
            
            return {
                'total_chamados': total_chamados,
                'total_abertos': total_abertos,
                'total_fechados': total_fechados,
                'tempo_medio_resolucao': tempo_medio,
                'chamados_por_tecnico': chamados_por_tecnico,
                'categorias': categorias,
                'tabela': tabela_dados,
                'insights': insights,
                'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'fonte': 'Supabase'
            }
            
        except Exception as e:
            print(f"❌ Erro no cálculo de métricas: {str(e)}")
            # Retorna estrutura mínima em caso de erro
            return {
                'total_chamados': len(df) if df is not None else 0,
                'total_abertos': 0,
                'total_fechados': 0,
                'tempo_medio_resolucao': 'N/A',
                'chamados_por_tecnico': {},
                'categorias': {},
                'tabela': [],
                'insights': {
                    'melhor_tecnico': 'Dados insuficientes',
                    'categoria_predominante': 'Dados insuficientes',
                    'tendencia_satisfacao': 'Dados insuficientes'
                },
                'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'fonte': 'Supabase'
            }
    
    def _generate_insights(self, df: pd.DataFrame, chamados_por_tecnico: Dict, categorias: Dict) -> Dict[str, str]:
        """Gera insights automáticos baseados nos dados"""
        insights = {}
        
        try:
            # Insight sobre melhor técnico
            if chamados_por_tecnico:
                melhor_tecnico = max(chamados_por_tecnico.items(), key=lambda x: x[1])
                insights['melhor_tecnico'] = f"🏆 {melhor_tecnico[0]} foi o técnico mais produtivo com {melhor_tecnico[1]} chamados."
            else:
                insights['melhor_tecnico'] = "📊 Dados de técnicos não disponíveis."
            
            # Insight sobre categoria predominante
            if categorias:
                categoria_principal = max(categorias.items(), key=lambda x: x[1])
                porcentagem = (categoria_principal[1] / sum(categorias.values())) * 100
                insights['categoria_predominante'] = f"📈 {categoria_principal[0]} representa {porcentagem:.1f}% dos chamados ({categoria_principal[1]} ocorrências)."
            else:
                insights['categoria_predominante'] = "📊 Dados de categorias não disponíveis."
            
            # Insight sobre satisfação
            if 'satisfacao' in df.columns:
                satisfacao_media = df['satisfacao'].mean()
                if not pd.isna(satisfacao_media):
                    if satisfacao_media >= 4.0:
                        insights['tendencia_satisfacao'] = f"😊 Excelente! Satisfação média de {satisfacao_media:.1f}/5 - clientes muito satisfeitos."
                    elif satisfacao_media >= 3.0:
                        insights['tendencia_satisfacao'] = f"🙂 Satisfação média de {satisfacao_media:.1f}/5 - há espaço para melhorias."
                    else:
                        insights['tendencia_satisfacao'] = f"😟 Atenção! Satisfação baixa de {satisfacao_media:.1f}/5 - revisar processos."
                else:
                    insights['tendencia_satisfacao'] = "📊 Dados de satisfação não disponíveis."
            else:
                insights['tendencia_satisfacao'] = "📊 Dados de satisfação não disponíveis."
            
        except Exception as e:
            print(f"⚠️ Aviso na geração de insights: {str(e)}")
            insights = {
                'melhor_tecnico': 'Erro na análise',
                'categoria_predominante': 'Erro na análise',
                'tendencia_satisfacao': 'Erro na análise'
            }
        
        return insights
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Coleta diagnósticos da integração com Supabase"""
        diag = {
            'url': self.url,
            'connected': False,
            'table_exists': False,
            'row_count': 0,
            'columns': []
        }
        
        try:
            # Testa conexão e acesso à tabela
            response = self.client.table('chamados').select('*', count='exact').limit(1).execute()
            
            diag['connected'] = True
            diag['table_exists'] = True
            diag['row_count'] = response.count if hasattr(response, 'count') else len(response.data)
            
            if response.data:
                diag['columns'] = list(response.data[0].keys())
            
        except Exception as e:
            diag['error'] = str(e)
            diag['hint'] = 'Verifique se a tabela "chamados" existe no Supabase e se as credenciais estão corretas.'
        
        return diag


def create_supabase_client():
    """Factory function para criar cliente Supabase"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise Exception("SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env")
    
    return SupabaseIntegration(url, key)
