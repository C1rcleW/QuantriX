/** Chart panel — renders statistical charts from analysis results. */

import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface ChartSpec {
  chart_type: "histogram" | "bar" | "grouped_bar" | "scatter" | "scatter_with_line" | "box";
  title: string;
  x_label: string;
  y_label: string;
  data?: Record<string, unknown>[];
  density?: Record<string, unknown>[];
  line?: Record<string, unknown>[];
  ci_upper?: number[];
  ci_lower?: number[];
  series?: { name: string; data: number[] }[];
  categories?: string[];
}

const COLORS = ["#1a73e8", "#34a853", "#ea4335", "#fbbc04", "#9c27b0", "#00bcd4"];

function HistogramChart({ spec }: { spec: ChartSpec }) {
  const data = spec.data || [];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 32, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="x" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={60} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="count" fill={COLORS[0]} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function SimpleBarChart({ spec }: { spec: ChartSpec }) {
  const data = spec.data || [];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 32, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={60} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="value" fill={COLORS[1]} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function GroupedBarChart({ spec }: { spec: ChartSpec }) {
  const series = spec.series || [];
  const categories: string[] = (spec.categories as string[]) || (spec.data as unknown as string[] || []);
  const rows = categories.map((cat, i) => {
    const row: Record<string, unknown> = { name: cat };
    series.forEach((s) => { row[s.name] = s.data[i] ?? 0; });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 32, left: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((s, i) => (
          <Bar key={s.name} dataKey={s.name} fill={COLORS[i % COLORS.length]} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

function ScatterPlot({ spec }: { spec: ChartSpec }) {
  const points = spec.data || [];
  const line = spec.line;

  if (line) {
    const scatterData = (points as Record<string, unknown>[]).map((p) => ({ x: Number(p.x), y: Number(p.y) }));
    const lineData = (line as Record<string, unknown>[]).map((p) => ({ x: Number(p.x), y: Number(p.y) }));
    return (
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart margin={{ top: 8, right: 16, bottom: 32, left: 48 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="x" tick={{ fontSize: 11 }} label={{ value: spec.x_label, position: "bottom", fontSize: 12 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: spec.y_label, angle: -90, position: "left", fontSize: 12 }} />
          <Tooltip />
          <Scatter name="observed" data={scatterData} fill={COLORS[0]} opacity={0.5} />
          <Line name="fitted" data={lineData} dataKey="y" stroke={COLORS[2]} dot={false} strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 8, right: 16, bottom: 32, left: 48 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="x" tick={{ fontSize: 11 }} label={{ value: spec.x_label, position: "bottom", fontSize: 12 }} />
        <YAxis dataKey="y" tick={{ fontSize: 11 }} label={{ value: spec.y_label, angle: -90, position: "left", fontSize: 12 }} />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
        <Scatter data={(points as Record<string, unknown>[]).map((p) => ({ x: Number(p.x), y: Number(p.y) }))} fill={COLORS[0]} opacity={0.6} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

function BoxPlot({ spec }: { spec: ChartSpec }) {
  const data = (spec.data || []) as Record<string, unknown>[];
  if (!data.length) return null;
  const chartH = 260;
  const margin = { top: 20, right: 30, bottom: 50, left: 60 };
  const plotW = 600;
  const plotH = chartH - margin.top - margin.bottom;
  const n = data.length;
  const barW = Math.min(60, (plotW - 60) / n * 0.6);
  const allVals = data.flatMap((d) => [
    Number(d.min), Number(d.max), Number(d.whisker_low), Number(d.whisker_high),
    ...(d.outliers as number[] || []),
  ]);
  const vMin = Math.min(...allVals);
  const vMax = Math.max(...allVals);
  const range = vMax - vMin || 1;
  const scaleY = (v: number) => margin.top + plotH - ((v - vMin) / range) * plotH;
  const xCenter = (i: number) => margin.left + (plotW / n) * (i + 0.5);

  return (
    <div style={{ width: "100%", maxWidth: 700, margin: "0 auto" }}>
      <svg viewBox={`0 0 ${plotW + margin.left + margin.right} ${chartH}`} style={{ width: "100%", height: chartH }}>
        {/* Y grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const y = scaleY(vMin + range * frac);
          return (
            <g key={frac}>
              <line x1={margin.left} y1={y} x2={margin.left + plotW} y2={y} stroke="#f0f0f0" strokeDasharray="3 3" />
              <text x={margin.left - 6} y={y + 4} textAnchor="end" fontSize={11} fill="#888">
                {(vMin + range * frac).toFixed(2)}
              </text>
            </g>
          );
        })}
        {/* Boxes */}
        {data.map((d, i) => {
          const cx = xCenter(i);
          const q1y = scaleY(Number(d.q1));
          const medY = scaleY(Number(d.median));
          const q3y = scaleY(Number(d.q3));
          const wLow = scaleY(Number(d.whisker_low));
          const wHigh = scaleY(Number(d.whisker_high));
          const color = COLORS[i % COLORS.length];
          return (
            <g key={i}>
              <line x1={cx - barW / 2} y1={wLow} x2={cx + barW / 2} y2={wLow} stroke={color} strokeWidth={1} />
              <line x1={cx} y1={wLow} x2={cx} y2={q1y} stroke={color} strokeWidth={1.5} />
              <rect x={cx - barW / 2} y={q3y} width={barW} height={q1y - q3y} fill={color} opacity={0.3} stroke={color} />
              <line x1={cx - barW / 2} y1={medY} x2={cx + barW / 2} y2={medY} stroke={color} strokeWidth={2} />
              <line x1={cx} y1={q3y} x2={cx} y2={wHigh} stroke={color} strokeWidth={1.5} />
              <line x1={cx - barW / 2} y1={wHigh} x2={cx + barW / 2} y2={wHigh} stroke={color} strokeWidth={1} />
              {(d.outliers as number[] || []).map((o, j) => (
                <circle key={j} cx={cx} cy={scaleY(o)} r={3} fill={color} opacity={0.5} />
              ))}
              <text x={cx} y={margin.top + plotH + 16} textAnchor="middle" fontSize={11} fill="#555">
                {String(d.name)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function ChartPanel({ charts }: { charts: ChartSpec[] }) {
  if (!charts || charts.length === 0) return null;

  return (
    <div style={{ marginTop: 16 }}>
      {charts.map((spec, i) => (
        <div key={i} style={{ marginBottom: 20, border: "1px solid #e0e0e0", borderRadius: 8, padding: 12, background: "#fff" }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#444", marginBottom: 8 }}>{spec.title}</div>
          {spec.chart_type === "histogram" && <HistogramChart spec={spec} />}
          {spec.chart_type === "bar" && <SimpleBarChart spec={spec} />}
          {spec.chart_type === "grouped_bar" && <GroupedBarChart spec={spec} />}
          {(spec.chart_type === "scatter" || spec.chart_type === "scatter_with_line") && <ScatterPlot spec={spec} />}
          {spec.chart_type === "box" && <BoxPlot spec={spec} />}
        </div>
      ))}
    </div>
  );
}
