# TechHelp Dashboard 📊

> Dashboard profissional de análise de chamados com tema GitHub Dark

## 🚀 Deploy Rápido

[![Deploy com Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Nicolas-AS07/Dashboard_Analise_de_Chamados)

**Veja o guia completo:** [DEPLOY_GUIDE.md](./DEPLOY_GUIDE.md)

## Visão Geral
Dashboard interativo para análise de indicadores de desempenho da equipe de suporte técnico da **TechHelp Solutions**. 

**Arquitetura moderna serverless:**
```
Google Drive/Sheets → Supabase Edge Function (sync auto) → PostgreSQL → API Flask → Dashboard SPA
```

## 🎯 Funcionalidades
- ✅ **KPIs em Tempo Real**: Total de chamados abertos/fechados, tempo médio de resolução
- ✅ **Gráficos Interativos**: Chamados por técnico e categorias mais recorrentes (com cores profissionais)
- ✅ **Tabela Dinâmica**: Status e satisfação dos clientes
- ✅ **Insights Automáticos**: Descrições geradas automaticamente abaixo dos gráficos
- ✅ **Sync Automático**: Edge Function sincroniza Drive → Supabase a cada 15 minutos
- ✅ **Design Profissional**: Tema GitHub Dark com logo SVG customizada
- ✅ **Alta Performance**: <100ms de resposta (vs 3-5s antes)

## 🏗️ Arquitetura

### Componentes

1. **Google Drive/Sheets** (Fonte de dados)
   - Planilha com dados de chamados
   - Atualizada manualmente ou por processos externos

2. **Supabase Edge Function** (Sync automático)
   - TypeScript/Deno serverless
   - Lê Google Sheets API e faz upsert no PostgreSQL
   - Agendada via `pg_cron` (a cada 15 min)

3. **Supabase PostgreSQL** (Database)
   - Tabela `chamados` com RLS e índices
   - Alta performance para leitura

4. **API Flask** (Backend)
   - Lê do Supabase (não mais do Drive direto!)
   - Cache de 5 minutos
   - Processamento de métricas e KPIs

5. **Frontend SPA** (Dashboard)
   - HTML/CSS/JS puro
   - Chart.js v4 para gráficos
   - Tema GitHub Dark profissional
   - Logo SVG customizada

### Estrutura do Projeto
```
Dashboard_Analise_de_Chamados/
├── supabase/                      # Infraestrutura Supabase
│   ├── functions/
│   │   └── sync-drive-data/      # Edge Function (sync automático)
│   │       ├── index.ts          # Lógica principal
│   │       ├── deno.json         # Config Deno
│   │       ├── .env.example      # Secrets necessários
│   │       └── README.md         # Docs da função
│   └── migrations/
│       └── 20250104_setup_pg_cron_sync.sql  # Config pg_cron
├── api/                           # Backend Flask
│   ├── app.py                    # Servidor principal
│   ├── supabase_client.py        # Cliente Supabase
│   └── requirements.txt          # Dependências Python
├── frontend/                      # Frontend SPA
│   ├── index.html               # Página principal
│   ├── css/
│   │   └── style.css            # Estilos personalizados
│   └── js/
│       └── dashboard.js         # Lógica do dashboard
├── config/                       # Configurações
│   └── .env.example             # Variáveis de ambiente
├── SETUP_SUPABASE.md            # 📘 Guia completo de setup
└── README.md                    # Este arquivo
```

## 🚀 Quick Start

### 📘 Setup Completo (Primeira vez)

**Leia o guia detalhado**: [SETUP_SUPABASE.md](./SETUP_SUPABASE.md)

**Resumo dos passos**:
1. Criar projeto no Supabase
2. Criar tabela `chamados` (SQL fornecido)
3. Configurar Google API Key
4. Deploy da Edge Function
5. Configurar pg_cron para sync automático
6. Executar API e Dashboard

### ⚡ Desenvolvimento Local (após setup)

#### 1. Clone o Repositório
```bash
git clone https://github.com/Nicolas-AS07/Dashboard_Analise_de_Chamados.git
cd Dashboard_Analise_de_Chamados
```

#### 2. Configurar Backend
```bash
cd api
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp ../config/.env.example ../config/.env
# Edite config/.env com suas credenciais Supabase
```

#### 3. Executar Aplicação
```bash
# Backend (API Flask)
cd api
python app.py
# API rodando em http://localhost:5001

# Frontend (outro terminal)
cd frontend
python -m http.server 8080
# Dashboard em http://localhost:8080
```

### 🧪 Testar

```bash
# Health check
curl http://localhost:5001/api/health

# Diagnóstico
curl http://localhost:5001/api/diagnostics

# Dados
curl http://localhost:5001/api/chamados
```

## 🌐 Deploy em Produção

### Supabase Edge Function (Sync)
```bash
# Instalar CLI
npm install -g supabase

# Login e link
supabase login
supabase link --project-ref seu-project-ref

# Configurar secrets
supabase secrets set GOOGLE_API_KEY=sua-key
supabase secrets set GOOGLE_SHEETS_ID=id-da-planilha
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key

# Deploy
supabase functions deploy sync-drive-data
```

### Backend API (Render/Railway)
1. Conectar repositório
2. Variáveis de ambiente:
   ```
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-anon-key
   PORT=5001
   ```
3. Build: `cd api && pip install -r requirements.txt`
4. Start: `cd api && python app.py`

### Frontend (Netlify/Vercel)
1. Publish directory: `frontend`
2. Atualizar `dashboard.js` com URL da API de produção

## 📊 Fonte de Dados

### Estrutura da Planilha (Google Sheets)

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| ID do Chamado | Identificador único | TH-001 |
| Data de Abertura | Data de criação | 01/11/2025 |
| Data de Fechamento | Data de resolução | 02/11/2025 |
| Status | Estado atual | Aberto/Fechado |
| Prioridade | Urgência | Alta/Média/Baixa |
| Motivo/Categoria | Tipo de problema | Hardware/Software |
| Técnico | Responsável | João Silva |
| Satisfação | Avaliação | Ótimo/Bom/Ruim |
| TMA (minutos) | Tempo médio | 45 |

### Sync Automático
- **Frequência**: A cada 15 minutos (configurável)
- **Método**: Edge Function → Google Sheets API → PostgreSQL
- **Logs**: `supabase functions logs sync-drive-data`

## 🔧 Tecnologias Utilizadas

### Backend
- **API**: Python Flask 2.3.3 + Flask-CORS
- **Database**: Supabase PostgreSQL (supabase-py 2.3.0)
- **Data Processing**: Pandas 2.1.1, NumPy 1.26

### Sync Layer
- **Edge Function**: Deno/TypeScript (Supabase Edge Runtime)
- **Scheduler**: pg_cron + pg_net (PostgreSQL extensions)
- **API Integration**: Google Sheets API v4

### Frontend
- **Stack**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js 3.9.1
- **UI**: Design responsivo custom

### Infrastructure
- **Database & Functions**: Supabase (serverless)
- **Backend Deploy**: Render/Railway/Heroku
- **Frontend Deploy**: Netlify/Vercel/GitHub Pages

## 📈 APIs

### GET /api/chamados
Retorna dados processados da planilha:
```json
{
  "total_abertos": 12,
  "total_fechados": 48,
  "tempo_medio_resolucao": "3.5 dias",
  "chamados_por_tecnico": {"João": 14, "Maria": 10, "Carlos": 6},
  "categorias": {"Hardware": 15, "Software": 9, "Rede": 6},
  "tabela": [
    {"id": 1, "status": "Fechado", "satisfacao": 4},
    ...
  ]
}
```

## 🤝 Contribuição
1. Fork o projeto
2. Crie uma feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor
**Nicolas-AS07** - [GitHub](https://github.com/Nicolas-AS07)

---
*Desenvolvido com ❤️ para TechHelp Solutions*

## 🔒 Segurança e Boas Práticas com Segredos

- Nunca faça commit de chaves, tokens, JSON de Service Account ou arquivos `.env`.
- Use `config/.env.example` com placeholders e mantenha seu `.env` local fora do versionamento.
- Garanta que estes padrões estejam no `.gitignore`:

```
config/*.json
config/.env
*.env
```

- Configure variáveis sensíveis diretamente no provedor (Render, Railway, Netlify) via painel de secrets/env vars.
- Se algum segredo já tiver sido exposto, ROTACIONE as chaves no Google Cloud e atualize o ambiente.
- Prefira apontar `GOOGLE_APPLICATION_CREDENTIALS` para um caminho seguro/montado em runtime em vez de colar o conteúdo do JSON.