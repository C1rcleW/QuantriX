/** API client for Quantrix backend.

  All calls go to the local backend (proxied by Vite in dev,
  or served by the Electron main process in production).
*/

const BASE = "/api";

export interface VariableSummary {
  name: string;
  label: string;
  display_name: string;
  variable_type: "continuous" | "ordinal" | "nominal" | "string";
  n_valid: number;
  missing_count: number;
  missing_percentage: number;
  n_unique: number | null;
}

export interface ImportResponse {
  dataset_id: string;
  name: string;
  source_format: string;
  n_rows: number;
  n_columns: number;
  variables: VariableSummary[];
}

export interface VariableDetail extends VariableSummary {
  measure_level: string;
  missing_pattern: string;
  is_complete: boolean;
  is_categorical: boolean;
  is_continuous: boolean;
  value_labels: { value: number | string; label: string }[];
  has_more_labels: boolean;
  stats: {
    min: number | null;
    max: number | null;
    mean: number | null;
    std_dev: number | null;
  } | null;
}

export interface DatasetSummary {
  dataset_id: string;
  name: string;
  source_format: string;
  n_rows: number;
  n_columns: number;
  variable_count: number;
}

export interface TableResponse {
  dataset_id: string;
  total_rows: number;
  offset: number;
  limit: number;
  columns: string[];
  rows: (string | null)[][];
}

/** Upload a file and get the parsed dataset. */
export async function importFile(
  file: File
): Promise<ImportResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE}/data/import`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Import failed");
  }

  return res.json();
}

/** Get dataset summary. */
export async function getDataset(
  datasetId: string
): Promise<DatasetSummary> {
  const res = await fetch(`${BASE}/data/${datasetId}`);
  if (!res.ok) throw new Error("Dataset not found");
  return res.json();
}

/** Get all variables for a dataset. */
export async function getVariables(
  datasetId: string
): Promise<{ dataset_id: string; variables: VariableDetail[] }> {
  const res = await fetch(`${BASE}/data/${datasetId}/variables`);
  if (!res.ok) throw new Error("Variables not found");
  return res.json();
}

/** Get paginated data table. */
export async function getTable(
  datasetId: string,
  offset = 0,
  limit = 100
): Promise<TableResponse> {
  const res = await fetch(
    `${BASE}/data/${datasetId}/table?offset=${offset}&limit=${limit}`
  );
  if (!res.ok) throw new Error("Table not found");
  return res.json();
}

// ── Analysis endpoints ────────────────────────────

export interface PlanRecommendation {
  rank: number;
  method_name: string;
  display_name?: string;
  method_family: string;
  confidence: number;
  rationale: string;
  assumptions: string[];
  alternative_methods: string[];
  matched_variables: { dependent: string | null; independents: string[] };
}

export interface AnalysisPlan {
  question: string;
  question_type: string;
  design: string;
  recommendations: PlanRecommendation[];
}

export interface SafetyReport {
  method_name: string;
  is_clean: boolean;
  has_errors: boolean;
  has_warnings: boolean;
  errors: { rule: string; message: string; suggestion: string }[];
  warnings: { rule: string; message: string; suggestion: string }[];
  info: { rule: string; message: string }[];
}

export interface Interpretation {
  method_name: string;
  summary: string;
  detailed: string;
  key_findings: string[];
  limitations: string[];
}

/** Get analysis plan from a research question. */
export async function getAnalysisPlan(
  datasetId: string,
  question: string
): Promise<AnalysisPlan> {
  const res = await fetch(`${BASE}/analysis/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, question }),
  });
  if (!res.ok) throw new Error("Plan failed");
  return res.json();
}

/** Run safety check for a method + variables. */
export async function runSafetyCheck(
  datasetId: string,
  methodName: string,
  dependent: string | null,
  independents: string[]
): Promise<SafetyReport> {
  const res = await fetch(`${BASE}/safety/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: datasetId,
      method_name: methodName,
      dependent,
      independents,
    }),
  });
  if (!res.ok) throw new Error("Safety check failed");
  return res.json();
}

/** Get natural-language interpretation of results. */
export async function getInterpretation(
  methodName: string,
  statistics: Record<string, unknown>
): Promise<Interpretation> {
  const res = await fetch(`${BASE}/chat/interpret`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ method_name: methodName, statistics }),
  });
  if (!res.ok) throw new Error("Interpretation failed");
  return res.json();
}

/** Generate report from sections. */
export async function generateReport(
  title: string,
  sections: { heading: string; interpretation: string; safety_notes?: string[] }[],
  datasetInfo?: { name: string; n_rows: number; n_columns: number }
): Promise<{ markdown: string; html: string; section_count: number }> {
  const res = await fetch(`${BASE}/report/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, sections, dataset_info: datasetInfo }),
  });
  if (!res.ok) throw new Error("Report generation failed");
  return res.json();
}

/** Execute a statistical analysis and get real results. */
export async function executeAnalysis(
  datasetId: string,
  methodName: string,
  dependent: string | null,
  independents: string[]
): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE}/analysis/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, method_name: methodName, dependent, independents }),
  });
  if (!res.ok) throw new Error("Analysis execution failed");
  return res.json();
}
