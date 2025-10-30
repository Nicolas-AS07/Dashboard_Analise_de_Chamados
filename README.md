# TechHelp Dashboard 📊

## Visão Geral
Dashboard interativo para análise de indicadores de desempenho da equipe de suporte técnico da **TechHelp Solutions**. A aplicação consome dados diretamente de uma planilha do Google Drive e apresenta KPIs e gráficos em tempo real.

## 🎯 Funcionalidades
- ✅ **KPIs em Tempo Real**: Total de chamados abertos/fechados, tempo médio de resolução
- ✅ **Gráficos Interativos**: Chamados por técnico e categorias mais recorrentes
- ✅ **Tabela Dinâmica**: Status e satisfação dos clientes
- ✅ **Insights Automáticos**: Descrições geradas automaticamente abaixo dos gráficos
- ✅ **Design Responsivo**: Interface moderna e intuitiva

## 🏗️ Estrutura do Projeto
```
Dashboard_Analise_de_Chamados/
├── api/                    # Backend Flask
│   ├── app.py             # Servidor principal
│   ├── google_sheets.py   # Integração Google Sheets API
│   └── requirements.txt   # Dependências Python
├── frontend/              # Frontend SPA
│   ├── index.html        # Página principal
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── dashboard.js  # Lógica do dashboard
├── utils/                 # Utilitários
│   └── data_processor.py # Processamento de dados
├── config/               # Configurações
│   └── .env.example     # Exemplo de variáveis de ambiente
└── README.md            # Documentação
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- Node.js (opcional, para ferramentas de build)
- Conta Google com acesso à planilha

### 1. Clone o Repositório
```bash
git clone https://github.com/Nicolas-AS07/Dashboard_Analise_de_Chamados.git
cd Dashboard_Analise_de_Chamados
```

### 2. Configurar Backend
```bash
cd api
pip install -r requirements.txt
```

### 3. Configurar Credenciais Google (sem expor segredos)
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto e ative as APIs:
  - Google Drive API
  - Google Sheets API
3. Crie uma Service Account e baixe o arquivo JSON (NÃO compartilhe nem commit em repositórios)
4. Mantenha o JSON fora do repositório OU coloque-o em `config/service-account.json` garantindo que esteja no `.gitignore`
5. Configure as variáveis de ambiente (nunca commit o arquivo real `.env`):
```bash
cp config/.env.example config/.env
# Edite o arquivo .env com suas configurações
```

### 4. Executar Aplicação
```bash
# Backend (API)
cd api
python app.py

# Frontend
# Abra frontend/index.html no navegador ou use um servidor local
# Exemplo com Python:
cd frontend
python -m http.server 8080
```

## 🌐 Deploy

### Netlify/GitHub Pages (Frontend)
1. Faça push do código para o GitHub
2. Conecte o repositório ao Netlify
3. Configure as variáveis de ambiente no painel do Netlify

### Render/Railway (Backend)
1. Conecte o repositório ao Render
2. Configure as variáveis de ambiente (NUNCA cole conteúdo de chaves/JSON diretamente no README ou em commits):
  - `GOOGLE_SHEETS_ID`: <YOUR_DRIVE_FILE_ID>
  - `GOOGLE_APPLICATION_CREDENTIALS`: caminho/variável apontando para o JSON da Service Account (use secrets do provedor)

## 📊 Fonte de Dados

Defina o ID da planilha via variável de ambiente `GOOGLE_SHEETS_ID` (não publique esse ID em arquivos versionados). Ex.: `<YOUR_DRIVE_FILE_ID>`

### Estrutura Esperada:
| Campo | Descrição |
|-------|-----------|
| ID_Chamado | Identificador único |
| Data_Abertura | Data de abertura |
| Data_Fechamento | Data de encerramento |
| Técnico | Nome do responsável |
| Categoria | Tipo de problema |
| Status | Aberto / Fechado |
| Tempo_Resolucao | Tempo em horas/dias |
| Satisfacao | Nota de 1 a 5 |

## 🔧 Tecnologias Utilizadas
- **Backend**: Python Flask, Google APIs
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Deploy**: Netlify (Frontend) + Render (Backend)

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