/** Data mode — file import and variable overview. */

import { useCallback, useState } from "react";
import type { ImportResponse, VariableDetail, TableResponse } from "../../api/client";
import { getTable, getVariables, importFile } from "../../api/client";
import { useDataset } from "../App";
import { DataTable } from "../../features/data/DataTable";
import { ImportDropzone } from "../../features/data/ImportDropzone";
import { VariableCards } from "../../features/data/VariableCards";

interface DatasetState {
  datasetId: string;
  summary: ImportResponse;
  variables: VariableDetail[] | null;
  table: TableResponse | null;
}

export function DataMode() {
  const { setDataset: setCtxDataset } = useDataset();
  const [local, setLocal] = useState<DatasetState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImport = useCallback(async (file: File) => {
    setLoading(true); setError(null);
    try {
      const summary = await importFile(file);
      const ds: DatasetState = { datasetId: summary.dataset_id, summary, variables: null, table: null };
      setLocal(ds);
      const [vars, table] = await Promise.all([getVariables(summary.dataset_id), getTable(summary.dataset_id, 0, 100)]);
      const full = { datasetId: summary.dataset_id, summary, variables: vars.variables, table };
      setLocal(full);
      setCtxDataset({ datasetId: summary.dataset_id, name: summary.name, nRows: summary.n_rows, nColumns: summary.n_columns, variables: vars.variables });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }, [setCtxDataset]);

  if (loading) return <div style={S.center}><p>Loading...</p></div>;
  if (error) return <div style={S.center}><ImportDropzone onImport={handleImport} /><div style={S.error}>{error}</div></div>;
  if (!local) return <div style={S.center}><ImportDropzone onImport={handleImport} /></div>;

  return (
    <div style={S.container}>
      <div style={S.header}>
        <h2 style={{ margin: 0 }}>{local.summary.name}</h2>
        <span style={S.meta}>{local.summary.n_rows} rows x {local.summary.n_columns} columns · {local.summary.source_format.toUpperCase()}</span>
      </div>
      {local.variables && <VariableCards variables={local.variables} />}
      {local.table && <div style={{ marginTop: 32 }}><h3 style={{ fontSize: 14, fontWeight: 600, color: "#555", marginBottom: 8 }}>Data Preview</h3><DataTable table={local.table} /></div>}
    </div>
  );
}

const S: Record<string, React.CSSProperties> = {
  container: { padding: 24, maxWidth: 900 },
  center: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", padding: 24 },
  header: { marginBottom: 24 },
  meta: { fontSize: 13, color: "#888" },
  error: { marginTop: 16, padding: "12px 16px", background: "#fff0f0", border: "1px solid #fcc", borderRadius: 6, color: "#c00", fontSize: 13 },
};
