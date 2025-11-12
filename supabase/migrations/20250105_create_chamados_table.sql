-- Migration: Criar tabela chamados para receber dados do Google Sheets
-- Executar este SQL no SQL Editor do Supabase Dashboard

CREATE TABLE IF NOT EXISTS public.chamados (
    -- Chave primária
    id_chamado TEXT PRIMARY KEY,
    
    -- Informações temporais
    mes TEXT,
    ano TEXT,
    data_abertura TIMESTAMPTZ,
    data_fechamento TIMESTAMPTZ,
    
    -- Classificação do chamado
    origem TEXT,
    tipo_de_chamado TEXT,
    categoria TEXT,
    subcategoria TEXT,
    assunto TEXT,
    
    -- Atendimento
    tecnico TEXT,
    status TEXT,
    
    -- Métricas
    satisfacao INTEGER CHECK (satisfacao >= 1 AND satisfacao <= 5),
    tma NUMERIC(10, 2), -- Tempo Médio de Atendimento em horas
    
    -- Detalhes
    descricao TEXT,
    solucao TEXT,
    
    -- Metadados
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar índices para otimizar queries
CREATE INDEX IF NOT EXISTS idx_chamados_mes_ano ON public.chamados(mes, ano);
CREATE INDEX IF NOT EXISTS idx_chamados_tecnico ON public.chamados(tecnico);
CREATE INDEX IF NOT EXISTS idx_chamados_categoria ON public.chamados(categoria);
CREATE INDEX IF NOT EXISTS idx_chamados_status ON public.chamados(status);
CREATE INDEX IF NOT EXISTS idx_chamados_data_abertura ON public.chamados(data_abertura);
CREATE INDEX IF NOT EXISTS idx_chamados_satisfacao ON public.chamados(satisfacao);

-- Criar trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_chamados_updated_at
    BEFORE UPDATE ON public.chamados
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilitar RLS (Row Level Security) para segurança
ALTER TABLE public.chamados ENABLE ROW LEVEL SECURITY;

-- Criar policy para permitir leitura pública (para o dashboard)
CREATE POLICY "Permitir leitura pública de chamados"
    ON public.chamados
    FOR SELECT
    USING (true);

-- Criar policy para permitir insert/update apenas via service_role
CREATE POLICY "Permitir insert/update via service_role"
    ON public.chamados
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Verificar se a tabela foi criada
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'chamados'
ORDER BY ordinal_position;

-- OPCIONAL: Inserir dados de teste
/*
INSERT INTO public.chamados (
    id_chamado, mes, ano, origem, tipo_de_chamado,
    categoria, subcategoria, assunto, tecnico,
    satisfacao, tma, status
) VALUES (
    'TESTE-001', 'Janeiro', '2025', 'Email', 'Incidente',
    'Suporte Técnico', 'Hardware', 'Problema com impressora', 'João Silva',
    5, 2.5, 'Fechado'
);
*/
