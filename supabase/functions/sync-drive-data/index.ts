// Edge Function para sincronizar dados do Google Drive para Supabase
// Executada automaticamente via pg_cron

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.3";

const GOOGLE_SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets";

interface ChamadoRow {
  id_chamado: string;
  data_abertura: string | null;
  data_fechamento: string | null;
  status: string | null;
  prioridade: string | null;
  categoria: string | null;
  solucao: string | null;
  solicitante: string | null;
  tecnico: string | null;
  departamento: string | null;
  tempo_resolucao: number | null;
  frt_minutos: number | null;
  satisfacao: number | null;
}

// Função para normalizar nomes de colunas
function normalizeColumnName(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // Remove acentos
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

// Mapear colunas do Google Sheets para schema do banco
function mapColumns(headers: string[]): Record<string, number> {
  const mapping: Record<string, number> = {};
  
  headers.forEach((header, index) => {
    const normalized = normalizeColumnName(header);
    
    // Mapeamento de variações de nomes
    if (normalized.includes("id") && normalized.includes("chamado")) {
      mapping["id_chamado"] = index;
    } else if (normalized.includes("data") && normalized.includes("abertura")) {
      mapping["data_abertura"] = index;
    } else if (normalized.includes("data") && normalized.includes("fechamento")) {
      mapping["data_fechamento"] = index;
    } else if (normalized === "status") {
      mapping["status"] = index;
    } else if (normalized === "prioridade") {
      mapping["prioridade"] = index;
    } else if (normalized.includes("motivo") || normalized === "categoria") {
      mapping["categoria"] = index;
    } else if (normalized.includes("solucao")) {
      mapping["solucao"] = index;
    } else if (normalized.includes("solicitante")) {
      mapping["solicitante"] = index;
    } else if (normalized.includes("agente") || normalized.includes("responsavel") || normalized === "tecnico") {
      mapping["tecnico"] = index;
    } else if (normalized.includes("departamento")) {
      mapping["departamento"] = index;
    } else if (normalized.includes("tma") && normalized.includes("minutos")) {
      mapping["tempo_resolucao"] = index;
    } else if (normalized.includes("frt") && normalized.includes("minutos")) {
      mapping["frt_minutos"] = index;
    } else if (normalized.includes("satisfacao")) {
      mapping["satisfacao"] = index;
    }
  });
  
  return mapping;
}

// Converter satisfação textual para numérica
function convertSatisfacao(value: string | number): number | null {
  if (typeof value === "number") return value;
  if (!value) return null;
  
  const normalized = value.toString().toLowerCase().trim();
  const mapping: Record<string, number> = {
    "ruim": 1,
    "péssimo": 1,
    "pessimo": 1,
    "regular": 2,
    "médio": 3,
    "medio": 3,
    "bom": 4,
    "ótimo": 5,
    "otimo": 5,
    "excelente": 5
  };
  
  return mapping[normalized] || null;
}

// Converter data para formato ISO
function parseDate(value: string | null): string | null {
  if (!value) return null;
  
  try {
    // Tenta vários formatos comuns
    const formats = [
      /^(\d{2})\/(\d{2})\/(\d{4})/, // DD/MM/YYYY
      /^(\d{4})-(\d{2})-(\d{2})/, // YYYY-MM-DD
    ];
    
    for (const format of formats) {
      const match = value.match(format);
      if (match) {
        if (format.source.startsWith("^(\\d{2})")) {
          // DD/MM/YYYY
          return `${match[3]}-${match[2]}-${match[1]}`;
        } else {
          // YYYY-MM-DD
          return value;
        }
      }
    }
    
    return null;
  } catch {
    return null;
  }
}

// Processar linha de dados
function processRow(row: any[], columnMap: Record<string, number>): ChamadoRow | null {
  const idChamado = row[columnMap["id_chamado"]]?.toString().trim();
  
  if (!idChamado) return null; // Ignora linhas sem ID
  
  // Converter TMA de minutos para horas se necessário
  let tempoResolucao = null;
  if (columnMap["tempo_resolucao"] !== undefined) {
    const tmaValue = parseFloat(row[columnMap["tempo_resolucao"]]);
    if (!isNaN(tmaValue)) {
      // Se o valor médio é maior que 100, assume que está em minutos
      tempoResolucao = tmaValue > 100 ? tmaValue / 60 : tmaValue;
    }
  }
  
  return {
    id_chamado: idChamado,
    data_abertura: parseDate(row[columnMap["data_abertura"]]),
    data_fechamento: parseDate(row[columnMap["data_fechamento"]]),
    status: row[columnMap["status"]]?.toString().trim() || null,
    prioridade: row[columnMap["prioridade"]]?.toString().trim() || null,
    categoria: row[columnMap["categoria"]]?.toString().trim() || null,
    solucao: row[columnMap["solucao"]]?.toString().trim() || null,
    solicitante: row[columnMap["solicitante"]]?.toString().trim() || null,
    tecnico: row[columnMap["tecnico"]]?.toString().trim() || null,
    departamento: row[columnMap["departamento"]]?.toString().trim() || null,
    tempo_resolucao: tempoResolucao,
    frt_minutos: columnMap["frt_minutos"] !== undefined 
      ? parseFloat(row[columnMap["frt_minutos"]]) || null 
      : null,
    satisfacao: columnMap["satisfacao"] !== undefined 
      ? convertSatisfacao(row[columnMap["satisfacao"]]) 
      : null,
  };
}

serve(async (req) => {
  try {
    // Validar autenticação (apenas service_role ou função interna)
    const authHeader = req.headers.get("authorization");
    const serviceRoleKey = Deno.env.get("SERVICE_ROLE_KEY");
    
    // Permite chamadas internas (pg_cron) ou com service_role key
    const isInternalCall = authHeader?.includes(serviceRoleKey || "");
    
    if (!isInternalCall && req.headers.get("user-agent") !== "pg_cron") {
      return new Response(
        JSON.stringify({ error: "Unauthorized - Use service_role key" }),
        { status: 401, headers: { "Content-Type": "application/json" } }
      );
    }

    console.log("🔄 Iniciando sincronização Drive → Supabase...");

    // Configurações
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "https://ukivnuaacwxtqjffvcha.supabase.co";
    const supabaseKey = Deno.env.get("SERVICE_ROLE_KEY")!;
    const googleApiKey = Deno.env.get("GOOGLE_API_KEY")!;
    const spreadsheetId = Deno.env.get("GOOGLE_SHEETS_ID")!;
    
    if (!supabaseKey || !googleApiKey || !spreadsheetId) {
      throw new Error("Faltando SERVICE_ROLE_KEY, GOOGLE_API_KEY ou GOOGLE_SHEETS_ID nas env vars");
    }

    // Cliente Supabase com service_role (bypassa RLS)
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false
      },
      db: {
        schema: 'public'
      }
    });

    // Buscar dados do Google Sheets
    const range = "A1:ZZ"; // Pega todas as colunas
    const url = `${GOOGLE_SHEETS_API}/${spreadsheetId}/values/${range}?key=${googleApiKey}`;
    
    console.log("📥 Buscando dados do Google Sheets...");
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Erro ao buscar Google Sheets: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const rows = data.values || [];

    if (rows.length === 0) {
      return new Response(
        JSON.stringify({ message: "Planilha vazia", synced: 0 }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // Primeira linha são os headers
    const headers = rows[0];
    const columnMap = mapColumns(headers);
    
    console.log(`📋 Headers mapeados: ${JSON.stringify(columnMap)}`);

    // Processar linhas de dados (pula header)
    const chamados: ChamadoRow[] = [];
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const chamado = processRow(row, columnMap);
      if (chamado) {
        chamados.push(chamado);
      }
    }

    console.log(`✅ Processados ${chamados.length} chamados válidos`);

    // Fazer upsert no Supabase (bulk)
    if (chamados.length > 0) {
      const { data: upsertData, error: upsertError } = await supabase
        .from("chamados")
        .upsert(chamados, {
          onConflict: "id_chamado",
          ignoreDuplicates: false // Atualiza se já existe
        });

      if (upsertError) {
        throw new Error(`Erro ao fazer upsert: ${upsertError.message}`);
      }

      console.log(`💾 Upsert concluído: ${chamados.length} registros sincronizados`);
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: "Sincronização concluída com sucesso",
        synced: chamados.length,
        timestamp: new Date().toISOString()
      }),
      { 
        status: 200, 
        headers: { "Content-Type": "application/json" } 
      }
    );

  } catch (error) {
    console.error("❌ Erro na sincronização:", error);
    
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        status: 500, 
        headers: { "Content-Type": "application/json" } 
      }
    );
  }
});
