# 🚀 Guia de Deploy - TechHelp Dashboard

## 📋 Pré-requisitos

### 1. Configurar Google Cloud Console
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione existente
3. Ative as APIs necessárias:
   - Google Sheets API
   - Google Drive API

### 2. Criar Service Account
1. Vá para "IAM & Admin" > "Service Accounts"
2. Clique em "Create Service Account"
3. Preencha os detalhes:
   - Nome: `techhelp-dashboard`
   - Descrição: `Service account para TechHelp Dashboard`
4. Clique em "Create and Continue"
5. Pule as permissões (opcional)
6. Clique em "Done"

### 3. Baixar Credenciais
1. Clique na Service Account criada
2. Vá para a aba "Keys"
3. Clique em "Add Key" > "Create new key"
4. Selecione "JSON" e clique em "Create"
5. Salve o arquivo como `service-account.json`

### 4. Compartilhar Planilha
1. Abra a planilha do Google Sheets (ID: `1W_5JCPdcUkuwpjrN058saxdNSltA17ND`)
2. Clique em "Compartilhar"
3. Adicione o email da Service Account (client_email do JSON)
4. Dê permissão de "Viewer" ou "Editor"

## 🌐 Deploy Frontend (Netlify)

### Opção 1: Deploy via GitHub
1. Faça push do código para o GitHub
2. Acesse [Netlify](https://netlify.com)
3. Clique em "New site from Git"
4. Conecte seu repositório
5. Configure:
   - Build command: `echo 'Frontend pronto'`
   - Publish directory: `frontend`
6. Clique em "Deploy site"

### Opção 2: Deploy Manual
1. Acesse [Netlify](https://netlify.com)
2. Arraste a pasta `frontend` para o deploy area
3. Aguarde o deploy completar

### Configurar Variáveis de Ambiente (Netlify)
1. Vá para Site Settings > Environment Variables
2. Adicione:
   - `API_URL`: URL do seu backend (ex: `https://sua-api.onrender.com`)

## ⚙️ Deploy Backend (Render)

### 1. Preparar Repositório
1. Commit todos os arquivos (exceto credenciais)
2. Push para GitHub

### 2. Deploy no Render
1. Acesse [Render](https://render.com)
2. Clique em "New +" > "Web Service"
3. Conecte seu repositório
4. Configure:
   - Name: `techhelp-dashboard-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r api/requirements.txt`
   - Start Command: `cd api && python app.py`

### 3. Configurar Variáveis de Ambiente
1. Vá para Environment
2. Adicione:
   - `GOOGLE_SHEETS_ID`: `1W_5JCPdcUkuwpjrN058saxdNSltA17ND`
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Conteúdo completo do arquivo service-account.json
   - `FLASK_ENV`: `production`
   - `PORT`: `5000`
   - `CORS_ORIGINS`: URL do seu frontend Netlify

## 🔧 Deploy Alternativo (Railway)

### 1. Deploy Backend
1. Acesse [Railway](https://railway.app)
2. Conecte seu GitHub
3. Deploy o repositório
4. Configure as mesmas variáveis de ambiente do Render

## 🌍 Deploy Alternativo (InfinityFree)

### Frontend
1. Faça upload dos arquivos da pasta `frontend`
2. Configure o domínio
3. Teste o acesso

### Backend (Limitado)
- InfinityFree tem limitações para Python
- Recomendado usar Render ou Railway para backend

## ✅ Verificação Pós-Deploy

### 1. Teste Backend
```bash
curl https://sua-api-url.com/api/health
```

### 2. Teste Frontend
1. Acesse a URL do Netlify
2. Verifique se os dados carregam
3. Teste a atualização manual

### 3. Teste Integração Completa
1. Abra o dashboard
2. Clique em "Atualizar"
3. Verifique se os gráficos atualizam
4. Teste filtros da tabela

## 🔒 Segurança

### Variáveis de Ambiente Importantes
- ✅ Mantenha `service-account.json` fora do repositório
- ✅ Use variáveis de ambiente para credenciais
- ✅ Configure CORS adequadamente
- ✅ Use HTTPS em produção

### Permissões da Planilha
- ✅ Dê apenas permissão de leitura necessária
- ✅ Monitor acessos regularmente
- ✅ Rotacione credenciais periodicamente

## 🐛 Troubleshooting

### Erro: "Credenciais não encontradas"
- Verifique se `GOOGLE_APPLICATION_CREDENTIALS_JSON` está configurado
- Confirme que o JSON está completo e válido

### Erro: "Planilha não encontrada"
- Verifique se o ID da planilha está correto
- Confirme que a Service Account tem acesso

### Erro: "CORS"
- Configure `CORS_ORIGINS` com a URL do frontend
- Verifique se o frontend está acessando a URL correta

### Frontend não carrega dados
- Teste o endpoint da API diretamente
- Verifique o console do navegador para erros
- Confirme a URL da API no código JavaScript

## 📞 Suporte

Para suporte adicional:
1. Verifique os logs do Render/Railway
2. Teste localmente primeiro
3. Consulte a documentação do Google Sheets API
4. Abra uma issue no GitHub

## 🔄 Atualizações Futuras

Para atualizar o dashboard:
1. Faça as alterações no código
2. Commit e push para o GitHub
3. Render/Railway fará deploy automático
4. Netlify atualizará o frontend

---

✨ **Parabéns!** Seu TechHelp Dashboard está pronto para produção!