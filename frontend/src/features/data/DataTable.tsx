/** Simple data table preview. */

import type { TableResponse } from "../../api/client";

interface Props {
  table: TableResponse;
}

export function DataTable({ table }: Props) {
  const { columns, rows, total_rows, offset } = table;

  return (
    <div style={styles.wrapper}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>#</th>
            {columns.map((col) => (
              <th key={col} style={styles.th}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td style={styles.td}>{offset + i + 1}</td>
              {row.map((cell, j) => (
                <td key={j} style={styles.td}>
                  {cell ?? <span style={{ color: "#ccc" }}>—</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div style={styles.footer}>
        Showing {offset + 1}–{offset + rows.length} of {total_rows} rows
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    border: "1px solid #e8e8e8",
    borderRadius: 8,
    overflow: "hidden",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 13,
  },
  th: {
    textAlign: "left",
    padding: "8px 12px",
    background: "#f8f9fa",
    borderBottom: "1px solid #e0e0e0",
    fontWeight: 600,
    color: "#555",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "6px 12px",
    borderBottom: "1px solid #f0f0f0",
    whiteSpace: "nowrap",
    maxWidth: 200,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  footer: {
    padding: "8px 12px",
    fontSize: 12,
    color: "#888",
  },
};
