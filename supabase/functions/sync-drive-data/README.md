# Edge Function: sync-drive-data

Função serverless para sincronizar dados do Google Drive (Sheets/Excel) para o Supabase PostgreSQL automaticamente.

## 🎯 Funcionalidade

- **Lê** dados de planilha do Google Drive via Google Sheets API
- **Normaliza** headers e tipos de dados
- **Faz upsert** na tabela `chamados` do Supabase (idempotente)
- **Execução automática** via pg_cron (a cada 15 minutos)

## 📋 Pré-requisitos

1. **Google API Key** com Google Sheets API habilitada
2. **Planilha pública** ou compartilhada com "Qualquer pessoa com o link"
3. **Supabase CLI** instalado (`npm install -g supabase`)

## 🚀 Deploy

### 1. Instalar Supabase CLI

```bash
# Via NPM
npm install -g supabase

# Ou via Scoop (Windows)
scoop install supabase
```

### 2. Fazer Login

```bash
supabase login
```

### 3. Linkar ao Projeto

```bash
# Na raiz do repositório
supabase link --project-ref seu-project-ref
```

**Encontrar project-ref**: Dashboard Supabase → Settings → General → Reference ID

### 4. Configurar Secrets

```bash
# Google API Key
supabase secrets set GOOGLE_API_KEY=AIzaSyA_sua_key_aqui

# ID da planilha (URL: https://docs.google.com/spreadsheets/d/{ID}/edit)
supabase secrets set GOOGLE_SHEETS_ID=1q1vgzZnLhnVRWVBQPDrQDqgaIOVvOQjIkSq_HXJMMB4

# Service Role Key (Dashboard → Settings → API → service_role - nunca use anon key!)
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
```

**⚠️ Importante**: Use a **service_role_key**, não a anon key!

### 5. Deploy da Função

```bash
supabase functions deploy sync-drive-data
```

### 6. Verificar Deploy

```bash
# Listar funções
supabase functions list

# Ver logs
supabase functions logs sync-drive-data --tail
```

## 🧪 Testar

### Teste Local (Desenvolvimento)

```bash
# 1. Criar arquivo .env local
cd supabase/functions/sync-drive-data
cp .env.example .env
# Editar .env com suas credenciais

# 2. Servir função localmente
supabase functions serve sync-drive-data --env-file .env

# 3. Invocar (em outro terminal)
curl -X POST http://localhost:54321/functions/v1/sync-drive-data \
  -H "Authorization: Bearer sua-service-role-key"
```

### Teste em Produção

```bash
# Via Supabase CLI
supabase functions invoke sync-drive-data --no-verify-jwt

# Via curl
curl -X POST "https://seu-projeto.supabase.co/functions/v1/sync-drive-data" \
  -H "Authorization: Bearer sua-service-role-key"
```

**Resposta esperada**:
```json
{
  "success": true,
  "message": "Sincronização concluída com sucesso",
  "synced": 550,
  "timestamp": "2025-11-04T12:00:00.000Z"
}
```

## ⏰ Automação com pg_cron

Após o deploy da função, configure o pg_cron:

1. Abra **SQL Editor** no Supabase Dashboard
2. Execute o conteúdo de: `supabase/migrations/20250104_setup_pg_cron_sync.sql`
3. **Edite as linhas 28-32** com suas configurações:
   ```sql
   ALTER DATABASE postgres SET app.settings.api_url TO 'https://seu-projeto.supabase.co';
   ALTER DATABASE postgres SET app.settings.service_role_key TO 'sua-service-role-key';
   ```

### Monitorar Execuções Automáticas

```sql
-- Ver histórico de execuções
SELECT 
    jobid,
    status,
    return_message,
    start_time,
    end_time,
    end_time - start_time AS duration
FROM cron.job_run_details
WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'sync-drive-data-job')
ORDER BY start_time DESC
LIMIT 20;
```

### Alterar Frequência

```sql
-- Desagendar job atual
SELECT cron.unschedule('sync-drive-data-job');

-- Criar com nova frequência
-- */5 = a cada 5 minutos
-- */30 = a cada 30 minutos
-- 0 * = a cada hora
SELECT cron.schedule('sync-drive-data-job', '*/5 * * * *', $$ ... $$);
```

## 📊 Monitoramento

### Ver Logs em Tempo Real

```bash
supabase functions logs sync-drive-data --tail
```

### Ver Logs Específicos

```bash
# Últimas 100 linhas
supabase functions logs sync-drive-data --limit 100

# Logs de um período
supabase functions logs sync-drive-data --since "2025-11-04 10:00:00"
```

### Métricas Importantes

**Logs esperados em execução bem-sucedida**:
```
🔄 Iniciando sincronização Drive → Supabase...
📥 Buscando dados do Google Sheets...
📋 Headers mapeados: {"id_chamado":0,"data_abertura":1,...}
✅ Processados 550 chamados válidos
💾 Upsert concluído: 550 registros sincronizados
```

## 🐛 Troubleshooting

### Erro "403 Forbidden" (Google Sheets)

**Causa**: Planilha não é pública
**Solução**:
1. Abrir planilha no Google Drive
2. Compartilhar → "Qualquer pessoa com o link"
3. Permissão: "Visualizador"

### Erro "GOOGLE_API_KEY não configurada"

```bash
# Verificar secrets
supabase secrets list

# Reconfigurar se necessário
supabase secrets set GOOGLE_API_KEY=sua-key
```

### Erro "Unauthorized - Use service_role key"

**Causa**: Usando anon key ou nenhuma key
**Solução**: Use a `service_role_key`:
```bash
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key
```

### Sync Funciona Manual, mas pg_cron não Executa

```sql
-- 1. Verificar se job existe
SELECT * FROM cron.job WHERE jobname = 'sync-drive-data-job';

-- 2. Verificar configurações
SHOW app.settings.api_url;
SHOW app.settings.service_role_key;

-- 3. Ver últimas execuções e erros
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
```

### Performance Lenta

**Sintomas**: Sync demora >10 segundos
**Soluções**:
- Reduzir tamanho da planilha (remover colunas desnecessárias)
- Usar range específico: `A1:M1000` em vez de `A1:ZZ`
- Aumentar timeout da Edge Function (config: `function.json`)

## 📝 Estrutura de Dados

### Input (Google Sheets)

Headers esperados (variações são normalizadas):
- `ID do Chamado` → `id_chamado`
- `Data de Abertura` → `data_abertura`
- `Data de Fechamento` → `data_fechamento`
- `Status` → `status`
- `Prioridade` → `prioridade`
- `Motivo` / `Categoria` → `categoria`
- `Solução` → `solucao`
- `Solicitante` → `solicitante`
- `Agente Responsável` / `Técnico` → `tecnico`
- `Departamento` → `departamento`
- `TMA (minutos)` → `tempo_resolucao` (convertido para horas)
- `FRT (minutos)` → `frt_minutos`
- `Satisfação do Cliente` → `satisfacao` (texto → número)

### Conversões Automáticas

**Satisfação textual → numérica**:
- "Ruim" / "Péssimo" → 1
- "Regular" → 2
- "Médio" → 3
- "Bom" → 4
- "Ótimo" / "Excelente" → 5

**Datas**: `DD/MM/YYYY` → `YYYY-MM-DD`

**TMA**: Se mediana > 100, assume minutos e converte para horas

## 🔒 Segurança

- ✅ Função valida `Authorization` header
- ✅ Só aceita `service_role_key` ou chamadas internas (pg_cron)
- ✅ Secrets armazenados de forma segura no Supabase
- ✅ Planilha pode ser pública (somente leitura)

## 📈 Performance

| Métrica | Valor Típico |
|---------|--------------|
| Tempo de execução | 2-5 segundos |
| Cold start | <1 segundo |
| Throughput | 100-500 registros/s |
| Custo (500 chamados, 2x/hora) | ~$0.01/mês |

## 🔄 Ciclo de Vida

```
1. pg_cron agenda job (*/15 * * * *)
2. pg_cron invoca Edge Function via pg_net.http_post
3. Edge Function lê Google Sheets API
4. Normaliza e valida dados
5. Faz upsert bulk no PostgreSQL
6. Retorna resultado (success/error)
7. pg_cron registra execução em cron.job_run_details
```

## 📚 Referências

- [Supabase Edge Functions Docs](https://supabase.com/docs/guides/functions)
- [pg_cron Extension](https://supabase.com/docs/guides/database/extensions/pg_cron)
- [Google Sheets API](https://developers.google.com/sheets/api/guides/concepts)
