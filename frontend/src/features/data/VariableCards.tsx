/** Variable cards — a visual overview of each variable.

   Replaces SPSS's variable-view table with a card-based layout.
   Each card shows: name, type icon, completeness bar, and key stats.
*/

import type { VariableDetail } from "../../api/client";

interface Props {
  variables: VariableDetail[];
}

const TYPE_ICONS: Record<string, string> = {
  continuous: "📊",
  ordinal: "🔢",
  nominal: "🏷️",
  string: "📝",
};

const TYPE_COLORS: Record<string, string> = {
  continuous: "#e8f0fe",
  ordinal: "#fef7e0",
  nominal: "#fce8e6",
  string: "#e6f4ea",
};

export function VariableCards({ variables }: Props) {
  return (
    <div style={styles.grid}>
      {variables.map((v) => (
        <div key={v.name} style={styles.card}>
          <div style={styles.cardHeader}>
            <span style={styles.typeIcon}>
              {TYPE_ICONS[v.variable_type] || "❓"}
            </span>
            <span style={styles.varName} title={v.display_name}>
              {v.display_name}
            </span>
            <span
              style={{
                ...styles.typeBadge,
                background: TYPE_COLORS[v.variable_type] || "#eee",
              }}
            >
              {v.variable_type}
            </span>
          </div>

          {/* Completeness bar */}
          <div style={styles.barTrack}>
            <div
              style={{
                ...styles.barFill,
                width: `${100 - v.missing_percentage}%`,
                background:
                  v.missing_percentage > 20
                    ? "#f4b400"
                    : v.missing_percentage > 5
                    ? "#fbbc04"
                    : "#34a853",
              }}
            />
          </div>

          <div style={styles.stats}>
            <span>
              {v.n_valid} valid
              {v.missing_count > 0 && (
                <span style={{ color: "#d93025" }}>
                  {" · "}
                  {v.missing_count} missing ({v.missing_percentage.toFixed(0)}%)
                </span>
              )}
            </span>
            {v.n_unique != null && (
              <span style={{ color: "#888" }}>
                {v.n_unique} unique
              </span>
            )}
          </div>

          {v.value_labels.length > 0 && (
            <div style={styles.labels}>
              {v.value_labels.slice(0, 3).map((vl, i) => (
                <span key={i} style={styles.labelChip}>
                  {vl.value}={vl.label}
                </span>
              ))}
              {v.has_more_labels && (
                <span style={styles.labelChip}>+{v.value_labels.length - 3} more</span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── Styles ─────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: 12,
  },
  card: {
    padding: 16,
    background: "#fff",
    border: "1px solid #e8e8e8",
    borderRadius: 8,
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  typeIcon: {
    fontSize: 18,
  },
  varName: {
    fontWeight: 600,
    fontSize: 14,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    flex: 1,
  },
  typeBadge: {
    fontSize: 10,
    padding: "2px 6px",
    borderRadius: 4,
    color: "#555",
    flexShrink: 0,
  },
  barTrack: {
    height: 4,
    background: "#eee",
    borderRadius: 2,
    marginBottom: 8,
  },
  barFill: {
    height: 4,
    borderRadius: 2,
    transition: "width 0.3s",
  },
  stats: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 12,
    color: "#666",
    marginBottom: 8,
  },
  labels: {
    display: "flex",
    gap: 4,
    flexWrap: "wrap",
  },
  labelChip: {
    fontSize: 10,
    padding: "1px 6px",
    background: "#f5f5f5",
    borderRadius: 4,
    color: "#777",
  },
};
