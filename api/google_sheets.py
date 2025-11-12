"""
Integração com Google Sheets e Google Drive para TechHelp Dashboard
Responsável por autenticar e buscar dados da planilha de chamados
Suporta:
 - Google Sheets (nativo) via gspread
 - Arquivos Excel (.xlsx/.xls) armazenados no Google Drive via Drive API
"""
import os
import json
import gspread
import pandas as pd
import io
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from typing import Dict, Any, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import unicodedata


class GoogleSheetsIntegration:
    """Classe para integração com Google Sheets API"""
    
    def __init__(self, sheets_id: str, credentials_path: str):
        """
        Inicializa a integração com Google Sheets
        
        Args:
            sheets_id: ID da planilha do Google Sheets
            credentials_path: Caminho para o arquivo JSON das credenciais
        """
        self.sheets_id = sheets_id
        self.credentials_path = credentials_path
        self.gc = None
        self.drive_service = None
        self.creds = None
        self.worksheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica com Google APIs (Sheets e Drive) usando Service Account"""
        try:
            # Escopo necessário para ler planilhas
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Carrega credenciais do arquivo JSON
            if os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(
                    self.credentials_path, 
                    scopes=scope
                )
            else:
                # Para deploy, tenta carregar de variável de ambiente
                creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
                if creds_json:
                    creds_info = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(
                        creds_info, 
                        scopes=scope
                    )
                else:
                    raise Exception("Credenciais do Google não encontradas")
            
            # Autoriza cliente gspread
            self.creds = creds
            self.gc = gspread.authorize(creds)
            # Cria serviço do Google Drive para baixar arquivos Excel
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✅ Autenticação com Google APIs (Sheets/Drive) realizada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro na autenticação: {str(e)}")
            raise
    
    def get_spreadsheet_data(self, worksheet_name: str = None) -> pd.DataFrame:
        """
        Busca dados da planilha e retorna como DataFrame
        
        Args:
            worksheet_name: Nome da aba (se None, usa a primeira aba)
            
        Returns:
            DataFrame com os dados da planilha
        """
        try:
            # Identifica o tipo do arquivo no Drive
            file_meta = self._get_drive_file_metadata(self.sheets_id)
            mime_type = file_meta.get('mimeType', '')
            file_name = file_meta.get('name', self.sheets_id)

            # Se for um Google Sheets (mime type do Google Sheets), usa gspread
            if mime_type == 'application/vnd.google-apps.spreadsheet':
                spreadsheet = self.gc.open_by_key(self.sheets_id)
                # Seleciona a primeira aba se não especificada
                if worksheet_name:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                else:
                    worksheet = spreadsheet.sheet1

                # Obtém todos os valores
                data = worksheet.get_all_values()

                if not data:
                    raise Exception("Planilha vazia ou não encontrada")

                # Converte para DataFrame
                df = pd.DataFrame(data[1:], columns=data[0])
                # Remove linhas vazias
                df = df.dropna(how='all')
                print(f"✅ Dados (Google Sheets) carregados: {len(df)} registros encontrados")
                return df

            # Caso contrário, tenta baixar como Excel via Drive API
            if mime_type in [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ] or file_name.lower().endswith(('.xlsx', '.xls')):
                bytes_io = self._download_drive_file(self.sheets_id)
                # Lê a primeira aba (ou específica) com pandas
                df = pd.read_excel(bytes_io, sheet_name=worksheet_name if worksheet_name else 0, engine='openpyxl')

                # Se o arquivo tiver múltiplas abas e pandas retornar dict, pega a primeira
                if isinstance(df, dict):
                    first_key = list(df.keys())[0]
                    df = df[first_key]

                # Remove linhas totalmente vazias
                df = df.dropna(how='all')
                print(f"✅ Dados (Excel via Drive) carregados: {len(df)} registros encontrados")
                return df

            # Se tipo desconhecido, tenta fallback para Google Sheets por gspread
            spreadsheet = self.gc.open_by_key(self.sheets_id)
            worksheet = spreadsheet.sheet1
            data = worksheet.get_all_values()
            if not data:
                raise Exception("Arquivo não suportado ou vazio")
            df = pd.DataFrame(data[1:], columns=data[0])
            df = df.dropna(how='all')
            print(f"✅ Dados (fallback) carregados: {len(df)} registros encontrados")
            return df
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {str(e)}")
            raise

    def _get_drive_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Obtém metadados (mimeType, name) de um arquivo no Drive"""
        try:
            if not self.drive_service:
                raise Exception("Serviço do Google Drive não inicializado")
            meta = self.drive_service.files().get(fileId=file_id, fields='id, name, mimeType').execute()
            return meta
        except Exception as e:
            print(f"⚠️ Não foi possível obter metadados do arquivo Drive: {str(e)}")
            # Continua com tentativa de leitura via gspread como fallback
            return {}

    def _download_drive_file(self, file_id: str) -> io.BytesIO:
        """Baixa um arquivo do Google Drive e retorna como BytesIO"""
        try:
            if not self.drive_service:
                raise Exception("Serviço do Google Drive não inicializado")
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"⬇️  Download do Drive {int(status.progress() * 100)}%...")
            fh.seek(0)
            return fh
        except Exception as e:
            print(f"❌ Erro ao baixar arquivo do Drive: {str(e)}")
            raise
    
    def process_chamados_data(self) -> Dict[str, Any]:
        """
        Processa os dados da planilha e retorna métricas calculadas
        
        Returns:
            Dicionário com KPIs e dados processados
        """
        try:
            # Carrega dados da planilha
            df = self.get_spreadsheet_data()
            
            # Normaliza nomes das colunas: minúsculas, sem acentos, underscores
            df.columns = [self._normalize_column_name(col) for col in df.columns]
            
            # Mapeia possíveis variações de nomes de colunas (já normalizados)
            # Ex.: "Agente Responsável" -> agente_responsavel; "Satisfação do Cliente" -> satisfacao_do_cliente
            column_mapping = {
                'id_chamado': [
                    'id_chamado', 'id', 'chamado_id', 'numero', 'id_do_chamado'
                ],
                'data_abertura': [
                    'data_abertura', 'abertura', 'data_inicio', 'data_de_abertura'
                ],
                'data_fechamento': [
                    'data_fechamento', 'fechamento', 'data_fim', 'data_de_fechamento'
                ],
                'tecnico': [
                    'tecnico', 'responsavel', 'atendente', 'agente_responsavel'
                ],
                'categoria': [
                    'categoria', 'tipo', 'classificacao', 'motivo'
                ],
                'status': [
                    'status', 'situacao', 'estado'
                ],
                # tempo_resolucao será derivado de 'tma_minutos' se existir
                'tempo_resolucao': [
                    'tempo_resolucao', 'tempo', 'duracao', 'tma_minutos'
                ],
                'satisfacao': [
                    'satisfacao', 'nota', 'avaliacao', 'satisfacao_do_cliente'
                ]
            }
            
            # Renomeia colunas para padrão
            for standard_name, variations in column_mapping.items():
                for var in variations:
                    if var in df.columns:
                        df = df.rename(columns={var: standard_name})
                        break
            
            # Converte dados para tipos apropriados
            df = self._convert_data_types(df)
            
            # Calcula métricas
            metrics = self._calculate_metrics(df)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erro no processamento: {str(e)}")
            raise

    def get_diagnostics(self) -> Dict[str, Any]:
        """Coleta diagnósticos da integração (env, credenciais, acesso ao Drive/Sheets, headers)."""
        diag: Dict[str, Any] = {
            'sheets_id': self.sheets_id,
            'credentials_path': self.credentials_path,
            'credentials_exists': os.path.exists(self.credentials_path) if self.credentials_path else False,
            'service_account_email': getattr(self.creds, 'service_account_email', None),
            'drive_access': {'ok': False},
            'file': {},
            'headers': [],
            'sample_rows': 0
        }

        try:
            meta = self._get_drive_file_metadata(self.sheets_id)
            if meta:
                diag['file'] = {'name': meta.get('name'), 'mimeType': meta.get('mimeType')}
            else:
                diag['file'] = {'name': None, 'mimeType': None, 'note': 'metadados indisponíveis (sem acesso?)'}
        except Exception as e:
            diag['file_error'] = str(e)

        # Tenta ler somente cabeçalhos sem processar tudo
        try:
            file_meta = diag.get('file', {})
            mime = file_meta.get('mimeType') or ''
            # Excel no Drive
            if mime in [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ] or (file_meta.get('name') or '').lower().endswith(('.xlsx', '.xls')):
                bytes_io = self._download_drive_file(self.sheets_id)
                excel = pd.read_excel(bytes_io, sheet_name=0, nrows=5, engine='openpyxl')
                excel.columns = [self._normalize_column_name(c) for c in excel.columns]
                diag['headers'] = list(excel.columns)
                diag['sample_rows'] = len(excel)
                diag['drive_access']['ok'] = True
            else:
                # Tenta como Google Sheets
                ss = self.gc.open_by_key(self.sheets_id)
                ws = ss.sheet1
                values = ws.get_all_values()
                if values:
                    headers = [self._normalize_column_name(h) for h in values[0]]
                    diag['headers'] = headers
                    diag['sample_rows'] = min(5, max(0, len(values) - 1))
                diag['drive_access']['ok'] = True
        except Exception as e:
            diag['drive_access'] = {'ok': False, 'error': str(e)}

        return diag
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas para tipos de dados apropriados"""
        try:
            # Converte datas
            if 'data_abertura' in df.columns:
                df['data_abertura'] = pd.to_datetime(df['data_abertura'], errors='coerce')
            
            if 'data_fechamento' in df.columns:
                df['data_fechamento'] = pd.to_datetime(df['data_fechamento'], errors='coerce')
            
            # Converte satisfação para numérico se for possível
            if 'satisfacao' in df.columns:
                # Tenta mapear classificações textuais para escala 1-5
                satisf_map = {
                    'ruim': 1, 'regular': 2, 'medio': 3, 'médio': 3,
                    'bom': 4, 'otimo': 5, 'ótimo': 5, 'excelente': 5
                }
                df['satisfacao'] = df['satisfacao'].apply(lambda x: satisf_map.get(str(x).strip().lower(), x))
                df['satisfacao'] = pd.to_numeric(df['satisfacao'], errors='coerce')
            
            # Converte tempo de resolução (se vier em minutos por TMA)
            if 'tempo_resolucao' in df.columns:
                df['tempo_resolucao'] = pd.to_numeric(df['tempo_resolucao'], errors='coerce')
            else:
                # Se existir TMA em minutos (normalizado como tma_minutos)
                if 'tma_minutos' in df.columns:
                    df['tma_minutos'] = pd.to_numeric(df['tma_minutos'], errors='coerce')
                    # Deriva tempo_resolucao em horas a partir de minutos
                    df['tempo_resolucao'] = df['tma_minutos'] / 60.0
            
            return df
            
        except Exception as e:
            print(f"⚠️ Aviso na conversão de tipos: {str(e)}")
            return df
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula KPIs e métricas do dashboard"""
        try:
            # KPIs básicos
            total_chamados = len(df)
            
            # Filtra por status se a coluna existir
            if 'status' in df.columns:
                df['status'] = df['status'].str.lower().str.strip()
                total_abertos = len(df[df['status'].isin(['aberto', 'em andamento', 'pendente'])])
                total_fechados = len(df[df['status'].isin(['fechado', 'resolvido', 'concluido'])])
            else:
                total_abertos = total_chamados // 3  # Estimativa se não houver coluna status
                total_fechados = total_chamados - total_abertos
            
            # Tempo médio de resolução
            tempo_medio = "N/A"
            if 'tempo_resolucao' in df.columns:
                tempo_medio_num = df['tempo_resolucao'].mean()
                if not pd.isna(tempo_medio_num):
                    tempo_medio = f"{tempo_medio_num:.1f} horas"
            else:
                # Como fallback, se houver datas, calcula média em horas
                if 'data_abertura' in df.columns and 'data_fechamento' in df.columns:
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
            
            # Dados para tabela
            tabela_dados = []
            for _, row in df.iterrows():
                tabela_dados.append({
                    'id': row.get('id_chamado', 'N/A'),
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
                'tabela': tabela_dados[:50],  # Limita a 50 registros para performance
                'insights': insights,
                'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            
        except Exception as e:
            print(f"❌ Erro no cálculo de métricas: {str(e)}")
            # Retorna dados básicos em caso de erro
            return {
                'total_chamados': len(df),
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
                'ultima_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
    
    def _generate_insights(self, df: pd.DataFrame, chamados_por_tecnico: Dict, categorias: Dict) -> Dict[str, str]:
        """Gera insights automáticos baseados nos dados"""
        insights = {}
        
        try:
            # Insight sobre melhor técnico
            if chamados_por_tecnico:
                melhor_tecnico = max(chamados_por_tecnico.items(), key=lambda x: x[1])
                insights['melhor_tecnico'] = f"🏆 {melhor_tecnico[0]} foi o técnico mais produtivo com {melhor_tecnico[1]} chamados resolvidos."
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
                'melhor_tecnico': 'Erro na análise de técnicos',
                'categoria_predominante': 'Erro na análise de categorias',
                'tendencia_satisfacao': 'Erro na análise de satisfação'
            }
        
        return insights

    def _normalize_column_name(self, text: str) -> str:
        """Normaliza nomes de colunas: minúsculas, sem acentos, underscores, sem pontuação"""
        if not isinstance(text, str):
            text = str(text)
        # remove acentos/diacríticos
        nfkd = unicodedata.normalize('NFKD', text)
        no_accents = ''.join([c for c in nfkd if not unicodedata.category(c) == 'Mn'])
        # para segurança, remove caracteres não alfanuméricos (exceto underscore)
        base = no_accents.strip().lower().replace('ç', 'c')
        # substitui qualquer caractere não [a-z0-9] por underscore
        import re
        cleaned = re.sub(r'[^a-z0-9]+', '_', base)
        # remove underscores duplicados e bordas
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        return cleaned


def create_google_sheets_client():
    """Factory function para criar cliente Google Sheets"""
    sheets_id = os.getenv('GOOGLE_SHEETS_ID', '1W_5JCPdcUkuwpjrN058saxdNSltA17ND')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'config/service-account.json')
    
    return GoogleSheetsIntegration(sheets_id, credentials_path)