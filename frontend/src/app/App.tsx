/** Application shell with three-panel layout + shared dataset context. */

import { createContext, useContext, useState } from "react";
import { AnalysisMode } from "./modes/AnalysisMode";
import { DataMode } from "./modes/DataMode";
import { ReportMode } from "./modes/ReportMode";
import type { VariableDetail } from "../api/client";

/* ── Shared Dataset Context ──────────────────────────── */

export interface DatasetInfo {
  datasetId: string;
  name: string;
  nRows: number;
  nColumns: number;
  variables: VariableDetail[];
}

interface DatasetCtx {
  dataset: DatasetInfo | null;
  setDataset: (d: DatasetInfo | null) => void;
}

const DatasetContext = createContext<DatasetCtx>({
  dataset: null,
  setDataset: () => {},
});

export function useDataset() {
  return useContext(DatasetContext);
}

/* ── App Shell ────────────────────────────────────────── */

type Mode = "data" | "analysis" | "report";

export function App() {
  const [mode, setMode] = useState<Mode>("data");
  const [dataset, setDataset] = useState<DatasetInfo | null>(null);

  return (
    <DatasetContext.Provider value={{ dataset, setDataset }}>
      <div style={styles.shell}>
        <aside style={styles.sidebar}>
          <div style={styles.logo}>Quantrix</div>
          <nav style={styles.nav}>
            <button style={navStyle(mode === "data")} onClick={() => setMode("data")}>Data</button>
            <button style={navStyle(mode === "analysis")} onClick={() => setMode("analysis")}>Analysis</button>
            <button style={navStyle(mode === "report")} onClick={() => setMode("report")}>Report</button>
          </nav>
          <div style={styles.version}>v0.1.0</div>
        </aside>

        <main style={styles.center}>
          <div style={{ display: mode === "data" ? "block" : "none" }}><DataMode /></div>
          <div style={{ display: mode === "analysis" ? "block" : "none" }}><AnalysisMode /></div>
          <div style={{ display: mode === "report" ? "block" : "none" }}><ReportMode /></div>
        </main>

        <aside style={styles.rightPanel}><RightPanel mode={mode} /></aside>
      </div>
    </DatasetContext.Provider>
  );
}

function RightPanel({ mode }: { mode: Mode }) {
  if (mode !== "data") return null;
  return (
    <div style={{ padding: 16 }}>
      <h3 style={{ margin: 0, fontSize: 14, color: "#666" }}>Variable Details</h3>
      <p style={{ color: "#999", fontSize: 13 }}>Click a variable card to see details.</p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  shell: { display: "flex", height: "100vh", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", color: "#333" },
  sidebar: { width: 200, background: "#f8f9fa", borderRight: "1px solid #e0e0e0", display: "flex", flexDirection: "column", padding: 16 },
  logo: { fontSize: 20, fontWeight: 700, marginBottom: 32 },
  nav: { display: "flex", flexDirection: "column", gap: 4, flex: 1 },
  version: { fontSize: 11, color: "#999", marginTop: 16 },
  center: { flex: 1, overflow: "auto", background: "#fff" },
  rightPanel: { width: 280, borderLeft: "1px solid #e0e0e0", background: "#fafafa", overflow: "auto" },
};

function navStyle(active: boolean): React.CSSProperties {
  return { width: "100%", textAlign: "left", padding: "8px 12px", border: "none", borderRadius: 6, background: active ? "#e8ecf1" : "transparent", color: active ? "#1a73e8" : "#555", fontWeight: active ? 600 : 400, fontSize: 14, cursor: "pointer" };
}
