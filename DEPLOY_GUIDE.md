# Deploy do TechHelp Dashboard

## 🚀 Deploy na Vercel (Recomendado)

### Passo 1: Prepare o repositório
```bash
git add .
git commit -m "Preparar para deploy"
git push origin main
```

### Passo 2: Conecte com a Vercel
1. Acesse [vercel.com](https://vercel.com)
2. Faça login com sua conta GitHub
3. Clique em "Add New Project"
4. Selecione o repositório `Dashboard_Analise_de_Chamados`
5. Configure as variáveis de ambiente:
   - `DATA_SOURCE` = `supabase`
   - `SUPABASE_URL` = sua URL do Supabase
   - `SUPABASE_KEY` = sua chave do Supabase
   - `CORS_ORIGINS` = `*` (ou seu domínio específico)

### Passo 3: Deploy
- Clique em "Deploy"
- Aguarde 2-3 minutos
- Seu dashboard estará online! 🎉

---

## 🐍 Opção 2: Render (Python-friendly)

### Vantagens:
- ✅ Grátis para começar
- ✅ Suporte nativo para Python
- ✅ Banco de dados PostgreSQL grátis

### Passos:
1. Acesse [render.com](https://render.com)
2. Conecte seu repositório GitHub
3. Crie um "Web Service"
4. Configure:
   - **Build Command**: `pip install -r api/requirements.txt`
   - **Start Command**: `cd api && gunicorn app:app`
5. Adicione as variáveis de ambiente
6. Deploy!

---

## 📦 Opção 3: Railway

### Vantagens:
- ✅ Deploy com um clique
- ✅ $5 grátis/mês
- ✅ Muito fácil de usar

### Passos:
1. Acesse [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Selecione seu repositório
4. Railway detecta Python automaticamente
5. Adicione variáveis de ambiente
6. Deploy automático!

---

## ⚙️ Configuração necessária para TODOS os métodos:

### 1. Atualize o CORS no backend:
No arquivo `api/app.py`, certifique-se que está assim:
```python
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins, resources={r"/api/*": {"origins": "*"}})
```

### 2. Atualize a URL da API no frontend:
No arquivo `frontend/js/dashboard-v2.js`, linha ~11:
```javascript
this.apiUrl = window.location.hostname === 'localhost' 
    ? 'http://localhost:5001/api' 
    : '/api';  // Em produção, usa o mesmo domínio
```

### 3. Variáveis de ambiente necessárias:
```
DATA_SOURCE=supabase
SUPABASE_URL=https://sua-url.supabase.co
SUPABASE_KEY=sua-chave-aqui
CORS_ORIGINS=*
```

---

## 🎯 Minha Recomendação:

**Use a Vercel** porque:
- ✅ Mais rápida
- ✅ Deploy automático do GitHub
- ✅ Interface mais amigável
- ✅ 100% grátis
- ✅ HTTPS automático
- ✅ CDN global

---

## 📝 Próximos passos:

1. Commit e push do código
2. Criar conta na Vercel
3. Conectar repositório
4. Adicionar variáveis de ambiente
5. Deploy! 🚀

Seu dashboard estará acessível em: `https://seu-projeto.vercel.app`
