/** Report mode — view and export analysis reports. */

import { useDataset } from "../App";
import type { VariableDetail } from "../../api/client";

export function ReportMode() {
  const { dataset } = useDataset();

  if (!dataset) {
    return <div style={S.center}><p style={{ color: "#888" }}>No dataset loaded. Import data first, then run analyses in the <strong>Analysis</strong> tab.</p></div>;
  }

  return (
    <div style={S.container}>
      <h2 style={{ margin: "0 0 8px" }}>Report</h2>
      <p style={{ color: "#888", fontSize: 13, margin: "0 0 24px" }}>
        Dataset: <strong>{dataset.name}</strong> ({dataset.nRows} rows x {dataset.nColumns} columns)
      </p>

      <div style={S.card}>
        <h3 style={{ margin: "0 0 8px", fontSize: 15 }}>How to generate a report</h3>
        <ol style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8, fontSize: 13, color: "#555" }}>
          <li>Go to <strong>Analysis</strong> tab</li>
          <li>Type your research question and click Ask</li>
          <li>Select a recommended method</li>
          <li>Click <strong>Explain Results</strong> to get natural-language interpretation</li>
          <li>Click <strong>Report</strong> button to view the generated report</li>
        </ol>
      </div>

      <div style={{ marginTop: 16, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 14 }}>Variables in this dataset</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 8 }}>
          {dataset.variables.map((v: VariableDetail) => (
            <div key={v.name} style={{ padding: 8, background: "#f8f9fa", borderRadius: 6, fontSize: 12 }}>
              <div style={{ fontWeight: 600 }}>{v.display_name}</div>
              <div style={{ color: "#888" }}>{v.variable_type} · n={v.n_valid}{v.missing_count > 0 ? ` (${v.missing_count} missing)` : ""}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const S: Record<string, React.CSSProperties> = {
  container: { padding: 24, maxWidth: 900 },
  center: { display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#888" },
  card: { padding: 16, border: "1px solid #e0e0e0", borderRadius: 8, background: "#f8f9fa" },
};
