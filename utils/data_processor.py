"""
Utilitários para processamento de dados do TechHelp Dashboard
Funções auxiliares para limpeza, transformação e análise de dados
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DataProcessor:
    """Classe para processamento e análise de dados de chamados"""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza um DataFrame
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame limpo e padronizado
        """
        # Remove espaços extras em strings
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        # Substitui valores vazios por None
        df = df.replace(['', ' ', 'NaN', 'nan', 'null'], None)
        
        return df
    
    @staticmethod
    def standardize_status(status: str) -> str:
        """
        Padroniza valores de status
        
        Args:
            status: Status original
            
        Returns:
            Status padronizado
        """
        if not status or pd.isna(status):
            return 'Indefinido'
        
        status = str(status).lower().strip()
        
        # Mapeamento de status
        status_mapping = {
            'aberto': 'Aberto',
            'open': 'Aberto',
            'novo': 'Aberto',
            'pendente': 'Aberto',
            'aguardando': 'Aberto',
            'fechado': 'Fechado',
            'closed': 'Fechado',
            'resolvido': 'Fechado',
            'resolved': 'Fechado',
            'concluido': 'Fechado',
            'concluído': 'Fechado',
            'finalizado': 'Fechado',
            'em andamento': 'Em Andamento',
            'em_andamento': 'Em Andamento',
            'progress': 'Em Andamento',
            'processando': 'Em Andamento',
            'trabalhando': 'Em Andamento'
        }
        
        return status_mapping.get(status, status.title())
    
    @staticmethod
    def calculate_resolution_time(
        start_date: pd.Series, 
        end_date: pd.Series, 
        unit: str = 'hours'
    ) -> pd.Series:
        """
        Calcula tempo de resolução entre duas datas
        
        Args:
            start_date: Série com datas de início
            end_date: Série com datas de fim
            unit: Unidade de tempo ('hours', 'days', 'minutes')
            
        Returns:
            Série com tempos de resolução
        """
        # Converte para datetime se não for
        start_date = pd.to_datetime(start_date, errors='coerce')
        end_date = pd.to_datetime(end_date, errors='coerce')
        
        # Calcula diferença
        diff = end_date - start_date
        
        # Converte para unidade desejada
        if unit == 'hours':
            return diff.dt.total_seconds() / 3600
        elif unit == 'days':
            return diff.dt.days
        elif unit == 'minutes':
            return diff.dt.total_seconds() / 60
        else:
            return diff.dt.total_seconds()
    
    @staticmethod
    def categorize_satisfaction(satisfaction: float) -> str:
        """
        Categoriza satisfação em níveis
        
        Args:
            satisfaction: Nota de satisfação (1-5)
            
        Returns:
            Categoria da satisfação
        """
        if pd.isna(satisfaction):
            return 'Não Avaliado'
        
        satisfaction = float(satisfaction)
        
        if satisfaction >= 4.5:
            return 'Excelente'
        elif satisfaction >= 4.0:
            return 'Boa'
        elif satisfaction >= 3.0:
            return 'Regular'
        elif satisfaction >= 2.0:
            return 'Ruim'
        else:
            return 'Péssima'
    
    @staticmethod
    def generate_performance_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Gera métricas de performance dos técnicos
        
        Args:
            df: DataFrame com dados de chamados
            
        Returns:
            Dicionário com métricas de performance
        """
        metrics = {}
        
        if 'tecnico' not in df.columns:
            return metrics
        
        # Performance por técnico
        technician_stats = df.groupby('tecnico').agg({
            'id_chamado': 'count',
            'satisfacao': ['mean', 'count'],
            'tempo_resolucao': 'mean'
        }).round(2)
        
        # Achatando colunas multiindex
        technician_stats.columns = ['total_chamados', 'satisfacao_media', 'avaliacoes_count', 'tempo_medio']
        
        # Calculando eficiência (chamados resolvidos / tempo médio)
        technician_stats['eficiencia'] = (
            technician_stats['total_chamados'] / 
            technician_stats['tempo_medio'].fillna(1)
        ).round(2)
        
        # Ranking de técnicos
        metrics['ranking_volume'] = technician_stats.sort_values('total_chamados', ascending=False).to_dict('index')
        metrics['ranking_satisfacao'] = technician_stats.sort_values('satisfacao_media', ascending=False).to_dict('index')
        metrics['ranking_eficiencia'] = technician_stats.sort_values('eficiencia', ascending=False).to_dict('index')
        
        return metrics
    
    @staticmethod
    def detect_trends(df: pd.DataFrame, date_column: str = 'data_abertura') -> Dict[str, Any]:
        """
        Detecta tendências nos dados ao longo do tempo
        
        Args:
            df: DataFrame com dados
            date_column: Nome da coluna de data
            
        Returns:
            Dicionário com análise de tendências
        """
        trends = {}
        
        if date_column not in df.columns:
            return trends
        
        # Converte data
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df_valid = df.dropna(subset=[date_column])
        
        if len(df_valid) == 0:
            return trends
        
        # Agrupa por semana
        df_valid['semana'] = df_valid[date_column].dt.to_period('W')
        weekly_counts = df_valid.groupby('semana').size()
        
        # Calcula tendência (crescimento/decrescimento)
        if len(weekly_counts) >= 2:
            recent_avg = weekly_counts.tail(2).mean()
            previous_avg = weekly_counts.head(-2).mean() if len(weekly_counts) > 2 else weekly_counts.iloc[0]
            
            change_percent = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
            
            trends['volume_change'] = round(change_percent, 1)
            trends['trend_direction'] = 'crescente' if change_percent > 5 else 'decrescente' if change_percent < -5 else 'estável'
        
        # Picos de atividade
        if len(weekly_counts) > 0:
            max_week = weekly_counts.idxmax()
            min_week = weekly_counts.idxmin()
            
            trends['pico_atividade'] = {
                'semana': str(max_week),
                'chamados': int(weekly_counts.max())
            }
            
            trends['menor_atividade'] = {
                'semana': str(min_week),
                'chamados': int(weekly_counts.min())
            }
        
        return trends
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida qualidade dos dados
        
        Args:
            df: DataFrame para validar
            
        Returns:
            Relatório de qualidade dos dados
        """
        quality_report = {
            'total_rows': len(df),
            'columns': list(df.columns),
            'missing_data': {},
            'data_types': {},
            'issues': []
        }
        
        # Análise de dados faltantes
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_percent = (missing_count / len(df)) * 100
            
            quality_report['missing_data'][col] = {
                'count': int(missing_count),
                'percentage': round(missing_percent, 2)
            }
            
            # Marca como problema se > 30% faltando
            if missing_percent > 30:
                quality_report['issues'].append(f"Coluna '{col}' tem {missing_percent:.1f}% de dados faltantes")
        
        # Tipos de dados
        for col in df.columns:
            quality_report['data_types'][col] = str(df[col].dtype)
        
        # Verifica duplicatas
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            quality_report['issues'].append(f"Encontradas {duplicates} linhas duplicadas")
        
        # Verifica datas inválidas
        date_columns = ['data_abertura', 'data_fechamento']
        for col in date_columns:
            if col in df.columns:
                invalid_dates = pd.to_datetime(df[col], errors='coerce').isna().sum()
                if invalid_dates > 0:
                    quality_report['issues'].append(f"Coluna '{col}' tem {invalid_dates} datas inválidas")
        
        # Score de qualidade (0-100)
        issues_penalty = len(quality_report['issues']) * 10
        missing_penalty = sum([info['percentage'] for info in quality_report['missing_data'].values()]) / len(df.columns)
        
        quality_score = max(0, 100 - issues_penalty - missing_penalty)
        quality_report['quality_score'] = round(quality_score, 1)
        
        return quality_report
    
    @staticmethod
    def export_summary(data: Dict[str, Any], format: str = 'dict') -> Any:
        """
        Exporta resumo dos dados em diferentes formatos
        
        Args:
            data: Dados processados
            format: Formato de saída ('dict', 'json', 'dataframe')
            
        Returns:
            Dados no formato especificado
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_records': data.get('total_chamados', 0),
            'summary_stats': {
                'abertos': data.get('total_abertos', 0),
                'fechados': data.get('total_fechados', 0),
                'tempo_medio': data.get('tempo_medio_resolucao', 'N/A')
            },
            'top_performers': {},
            'insights': data.get('insights', {})
        }
        
        # Top performers
        if 'chamados_por_tecnico' in data:
            sorted_technicians = sorted(
                data['chamados_por_tecnico'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            summary['top_performers']['technicians'] = dict(sorted_technicians[:5])
        
        if 'categorias' in data:
            sorted_categories = sorted(
                data['categorias'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            summary['top_performers']['categories'] = dict(sorted_categories[:5])
        
        if format == 'json':
            import json
            return json.dumps(summary, indent=2, ensure_ascii=False)
        elif format == 'dataframe':
            return pd.DataFrame([summary])
        else:
            return summary


def create_sample_data() -> pd.DataFrame:
    """
    Cria dados de exemplo para testes
    
    Returns:
        DataFrame com dados de exemplo
    """
    np.random.seed(42)
    
    n_records = 50
    
    # Gera dados aleatórios mas realistas
    data = {
        'ID_Chamado': [f'TH{str(i).zfill(4)}' for i in range(1, n_records + 1)],
        'Data_Abertura': pd.date_range(start='2024-01-01', periods=n_records, freq='D'),
        'Data_Fechamento': [],
        'Tecnico': np.random.choice(['João Silva', 'Maria Santos', 'Carlos Oliveira', 'Ana Costa', 'Pedro Ferreira'], n_records),
        'Categoria': np.random.choice(['Hardware', 'Software', 'Rede', 'Sistema', 'Usuario'], n_records),
        'Status': np.random.choice(['Aberto', 'Fechado', 'Em Andamento'], n_records, p=[0.2, 0.6, 0.2]),
        'Satisfacao': np.random.choice([1, 2, 3, 4, 5, None], n_records, p=[0.05, 0.1, 0.15, 0.35, 0.25, 0.1])
    }
    
    # Gera datas de fechamento (só para chamados fechados)
    for i, status in enumerate(data['Status']):
        if status == 'Fechado':
            days_to_add = np.random.randint(1, 10)
            data['Data_Fechamento'].append(data['Data_Abertura'][i] + timedelta(days=days_to_add))
        else:
            data['Data_Fechamento'].append(None)
    
    df = pd.DataFrame(data)
    
    # Calcula tempo de resolução
    df['Tempo_Resolucao'] = DataProcessor.calculate_resolution_time(
        df['Data_Abertura'], 
        df['Data_Fechamento'], 
        unit='hours'
    )
    
    return df


if __name__ == "__main__":
    # Teste das funções utilitárias
    print("🧪 Testando utilitários de processamento...")
    
    # Cria dados de exemplo
    df = create_sample_data()
    print(f"✅ Dados de exemplo criados: {len(df)} registros")
    
    # Testa processamento
    processor = DataProcessor()
    
    # Valida qualidade
    quality = processor.validate_data_quality(df)
    print(f"✅ Qualidade dos dados: {quality['quality_score']}/100")
    
    # Detecta tendências
    trends = processor.detect_trends(df)
    print(f"✅ Tendências detectadas: {trends.get('trend_direction', 'N/A')}")
    
    # Métricas de performance
    metrics = processor.generate_performance_metrics(df)
    print(f"✅ Métricas calculadas para {len(metrics.get('ranking_volume', {}))} técnicos")
    
    print("🎉 Todos os testes passaram!")