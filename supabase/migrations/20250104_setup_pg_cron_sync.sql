-- Migration: Configurar pg_cron para sincronização automática Drive → Supabase
-- Executar este SQL no SQL Editor do Supabase Dashboard

-- 1. Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- 2. Garantir que pg_cron pode acessar o schema público
GRANT USAGE ON SCHEMA cron TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO postgres;

-- 3. Criar tabela para armazenar configurações (workaround para permissões Supabase)
CREATE TABLE IF NOT EXISTS public.sync_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Inserir configurações (SUBSTITUA COM SEUS VALORES REAIS!)
INSERT INTO public.sync_config (key, value)
VALUES 
    ('api_url', 'https://seu-projeto.supabase.co'),
    ('service_role_key', 'sua-service-role-key-aqui')
ON CONFLICT (key) 
DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- 5. Criar job que executa Edge Function a cada 15 minutos
SELECT cron.schedule(
    'sync-drive-data-job',                    -- Nome do job
    '*/15 * * * *',                           -- Cron: a cada 15 minutos
    $$
    SELECT
        net.http_post(
            url := (SELECT value FROM public.sync_config WHERE key = 'api_url') || '/functions/v1/sync-drive-data',
            headers := jsonb_build_object(
                'Content-Type', 'application/json',
                'Authorization', 'Bearer ' || (SELECT value FROM public.sync_config WHERE key = 'service_role_key')
            ),
            body := '{}'::jsonb
        ) AS request_id;
    $$
);

-- 6. Verificar configurações inseridas
SELECT * FROM public.sync_config;

-- 7. Verificar jobs agendados
SELECT * FROM cron.job;

-- 8. Ver histórico de execuções (últimas 10)
SELECT 
    jobid,
    runid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 10;

-- 9. OPCIONAL: Desabilitar job temporariamente
-- SELECT cron.unschedule('sync-drive-data-job');

-- 10. OPCIONAL: Alterar frequência do job
-- SELECT cron.unschedule('sync-drive-data-job');
-- SELECT cron.schedule('sync-drive-data-job', '*/5 * * * *', $$ ... $$); -- A cada 5 min

-- 11. OPCIONAL: Executar manualmente para testar
SELECT
    net.http_post(
        url := (SELECT value FROM public.sync_config WHERE key = 'api_url') || '/functions/v1/sync-drive-data',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer ' || (SELECT value FROM public.sync_config WHERE key = 'service_role_key')
        ),
        body := '{}'::jsonb
    ) AS request_id;

-- 12. OPCIONAL: Atualizar configurações depois
-- UPDATE public.sync_config SET value = 'nova-url' WHERE key = 'api_url';
-- UPDATE public.sync_config SET value = 'nova-key' WHERE key = 'service_role_key';
