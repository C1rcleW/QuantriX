/** Analysis mode — guided wizard + free text → plan → execute → safety → interpret → report. */

import { useCallback, useState } from "react";
import type { AnalysisExecutionResult, AnalysisPlan, Interpretation, PlanRecommendation, SafetyReport } from "../../api/client";
import { executeAnalysis, generateReport, getAnalysisPlan, getAnalysisPlanStructured, getInterpretation, runSafetyCheck } from "../../api/client";
import { useDataset } from "../App";

type InputMode = "guided" | "free";

interface GoalDef {
  key: string;
  label: string;
  desc: string;
  needsIv: boolean;
}

const GOALS: GoalDef[] = [
  { key: "describe", label: "Describe", desc: "Summarize a single variable", needsIv: false },
  { key: "compare_groups", label: "Compare Groups", desc: "Compare a variable across groups", needsIv: true },
  { key: "find_association", label: "Find Association", desc: "Find relationship between variables", needsIv: true },
  { key: "predict", label: "Predict", desc: "Predict one variable from another", needsIv: true },
];

function varTypeLabel(t: string): string {
  const map: Record<string, string> = { continuous: "# (cont.)", ordinal: "~ (ord.)", nominal: "= (cat.)", string: "T (text)" };
  return map[t] || t;
}

export function AnalysisMode() {
  const { dataset } = useDataset();
  const [mode, setMode] = useState<InputMode>("guided");
  const [question, setQuestion] = useState("");
  const [selectedGoal, setSelectedGoal] = useState<string>("describe");
  const [dvName, setDvName] = useState<string>("");
  const [ivName, setIvName] = useState<string>("");
  const [plan, setPlan] = useState<AnalysisPlan | null>(null);
  const [selectedMethod, setSelectedMethod] = useState<PlanRecommendation | null>(null);
  const [safety, setSafety] = useState<SafetyReport | null>(null);
  const [statResult, setStatResult] = useState<AnalysisExecutionResult | null>(null);
  const [interpretation, setInterpretation] = useState<Interpretation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasData = dataset && dataset.datasetId;
  const goalDef = GOALS.find(g => g.key === selectedGoal) || GOALS[0];
  const variables = dataset?.variables || [];

  const handleAskFree = useCallback(async () => {
    if (!question.trim() || !dataset) return;
    setLoading(true); setError(null); setPlan(null); setSafety(null); setStatResult(null); setInterpretation(null); setSelectedMethod(null);
    try {
      const result = await getAnalysisPlan(dataset.datasetId, question);
      setPlan(result);
      if (result.recommendations.length > 0) setSelectedMethod(result.recommendations[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally { setLoading(false); }
  }, [question, dataset]);

  const handleAskGuided = useCallback(async () => {
    if (!dataset) return;
    if (!dvName && selectedGoal !== "describe") return;
    setLoading(true); setError(null); setPlan(null); setSafety(null); setStatResult(null); setInterpretation(null); setSelectedMethod(null);
    try {
      const ivs = ivName ? [ivName] : [];
      const result = await getAnalysisPlanStructured(dataset.datasetId, selectedGoal, dvName || null, ivs);
      setPlan(result);
      if (result.recommendations.length > 0) setSelectedMethod(result.recommendations[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally { setLoading(false); }
  }, [dataset, selectedGoal, dvName, ivName]);

  const handleSelectAndRun = useCallback(async (rec: PlanRecommendation) => {
    if (!dataset) return;
    setSelectedMethod(rec); setSafety(null); setStatResult(null); setInterpretation(null); setError(null);
    try {
      const s = await runSafetyCheck(dataset.datasetId, rec.method_name, rec.matched_variables.dependent, rec.matched_variables.independents);
      setSafety(s);
    } catch { /* optional */ }
    try {
      const data = await executeAnalysis(dataset.datasetId, rec.method_name, rec.matched_variables.dependent, rec.matched_variables.independents);
      setStatResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis execution failed");
    }
  }, [dataset]);

  const handleInterpret = useCallback(async () => {
    if (!statResult || !selectedMethod) return;
    try {
      const stats: Record<string, unknown> = {
        dv_label: statResult.dv_label || selectedMethod.matched_variables.dependent || "outcome",
        iv_label: statResult.iv_label || (selectedMethod.matched_variables.independents[0] || "predictor"),
      };
      if (statResult.statistics && typeof statResult.statistics === "object") {
        Object.assign(stats, statResult.statistics as Record<string, unknown>);
      }
      if (statResult.effect_sizes && typeof statResult.effect_sizes === "object") {
        const es = statResult.effect_sizes as Record<string, unknown>;
        if ("cohens_d" in es) stats.cohens_d = es.cohens_d;
        if ("r" in es) stats.r = es.r;
        if ("eta_squared" in es) stats.eta_squared = es.eta_squared;
        if ("r_squared" in es) stats.r_squared = es.r_squared;
      }
      if (statResult.group_labels) stats.group_labels = statResult.group_labels;
      if (statResult.misc && typeof statResult.misc === "object") {
        Object.assign(stats, statResult.misc as Record<string, unknown>);
      }
      if (statResult.sig_text) stats.sig_text = statResult.sig_text;
      if (statResult.effect_size_text) stats.effect_size_text = statResult.effect_size_text;

      const interp = await getInterpretation(selectedMethod.method_name, stats);
      setInterpretation(interp);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Interpretation failed");
    }
  }, [statResult, selectedMethod]);

  const handleReport = useCallback(async () => {
    if (!interpretation || !dataset) return;
    try {
      const report = await generateReport(`${dataset.name} Analysis`, [
        { heading: selectedMethod?.method_name || "Results", interpretation: interpretation.detailed || interpretation.summary, safety_notes: interpretation.limitations },
      ], { name: dataset.name, n_rows: dataset.nRows, n_columns: dataset.nColumns });
      const blob = new Blob([report.markdown], { type: "text/markdown" });
      window.open(URL.createObjectURL(blob), "_blank");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report failed");
    }
  }, [interpretation, dataset, selectedMethod]);

  if (!hasData) {
    return <div style={S.center}><p style={{ color: "#888" }}>No dataset loaded. Switch to <strong>Data</strong> tab and import a file first.</p></div>;
  }

  const resetWizard = () => {
    setSelectedGoal("describe"); setDvName(""); setIvName("");
    setPlan(null); setSafety(null); setStatResult(null); setInterpretation(null); setSelectedMethod(null); setError(null);
  };

  return (
    <div style={S.container}>
      <div style={S.header}>
        <h2 style={{ margin: 0 }}>Research Planner</h2>
        <span style={S.meta}>{dataset.name} ({dataset.nRows} x {dataset.nColumns})</span>
      </div>

      {/* Mode toggle */}
      <div style={S.tabRow}>
        <button style={tabStyle(mode === "guided")} onClick={() => { setMode("guided"); resetWizard(); }}>Guided</button>
        <button style={tabStyle(mode === "free")} onClick={() => { setMode("free"); resetWizard(); }}>Free Text</button>
      </div>

      {/* ── Guided Mode ── */}
      {mode === "guided" && (
        <div style={S.wizard}>
          {/* Step 1: Goal */}
          <div style={S.step}>
            <div style={S.stepLabel}>1. What do you want to know?</div>
            <div style={S.goalRow}>
              {GOALS.map(g => (
                <button key={g.key} style={goalBtnStyle(selectedGoal === g.key)} onClick={() => { setSelectedGoal(g.key); setDvName(""); setIvName(""); }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{g.label}</div>
                  <div style={{ fontSize: 11, opacity: 0.7 }}>{g.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: Variables */}
          <div style={S.step}>
            <div style={S.stepLabel}>2. Select variables</div>
            <div style={S.varRow}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>Variable to analyze</div>
                <select style={S.select} value={dvName} onChange={e => setDvName(e.target.value)}>
                  <option value="">-- select --</option>
                  {variables.map(v => (
                    <option key={v.name} value={v.name}>{v.display_name} {varTypeLabel(v.variable_type)}</option>
                  ))}
                </select>
              </div>

              {goalDef.needsIv && (
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>Group by / Compare with</div>
                  <select style={S.select} value={ivName} onChange={e => setIvName(e.target.value)}>
                    <option value="">-- select --</option>
                    {variables.filter(v => v.name !== dvName).map(v => (
                      <option key={v.name} value={v.name}>{v.display_name} {varTypeLabel(v.variable_type)}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>

          <button style={S.askBtn}
            onClick={handleAskGuided}
            disabled={loading || (selectedGoal !== "describe" && !dvName)}>
            {loading ? "Analyzing..." : "Ask"}
          </button>
        </div>
      )}

      {/* ── Free Text Mode ── */}
      {mode === "free" && (
        <div style={S.qbox}>
          <textarea style={S.input} placeholder="What do you want to know? e.g., Does gender affect income?" value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAskFree(); } }} rows={2} />
          <button style={S.askBtn} onClick={handleAskFree} disabled={loading || !question.trim()}>{loading ? "..." : "Ask"}</button>
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      {/* ── Results (shared) ── */}
      {plan && (
        <div>
          <h3 style={S.secTitle}>Recommended ({plan.question_type})</h3>
          {plan.recommendations.map(rec => (
            <div key={rec.rank} style={{ ...S.card, ...(selectedMethod?.method_name === rec.method_name ? S.cardSel : {}) }} onClick={() => handleSelectAndRun(rec)}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                <span style={{ fontSize: 11, color: "#999" }}>#{rec.rank}</span>
                <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{rec.method_name}</span>
                <span style={{ fontSize: 11, padding: "2px 8px", background: "#e8f0fe", borderRadius: 4, color: "#1a73e8" }}>{Math.round(rec.confidence * 100)}%</span>
              </div>
              <div style={{ fontSize: 12, color: "#666" }}>{rec.rationale}</div>
            </div>
          ))}
        </div>
      )}

      {selectedMethod && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
          <div style={S.panel}>
            <h3 style={S.secTitle}>Safety Check</h3>
            {safety ? (
              <div>
                {safety.is_clean && <div style={{ padding: 8, background: "#e6f4ea", borderRadius: 6, color: "#137333", fontSize: 13, fontWeight: 600, marginBottom: 8 }}>All checks passed</div>}
                {safety.errors.map((e, i) => <div key={i} style={{ padding: 6, background: "#fdecea", borderRadius: 6, marginBottom: 4, fontSize: 12 }}><strong>ERROR:</strong> {e.message}</div>)}
                {safety.warnings.map((w, i) => <div key={i} style={{ padding: 6, background: "#fef7e0", borderRadius: 6, marginBottom: 4, fontSize: 12 }}><strong>WARN:</strong> {w.message}</div>)}
              </div>
            ) : <div style={{ fontSize: 12, color: "#888" }}>Checking...</div>}
          </div>

          <div style={S.panel}>
            <h3 style={S.secTitle}>Results {statResult && <button style={S.reportBtn} onClick={handleReport}>Report</button>}</h3>
            {statResult ? (
              <div>
                <div style={{ fontSize: 12, color: "#333", marginBottom: 8 }}>
                  <strong>{statResult.sig_text}</strong>
                  {statResult.effect_size_text && <span> · {statResult.effect_size_text}</span>}
                </div>
                {statResult.tables && (statResult.tables as any[]).slice(0, 1).map((t: any, i: number) => (
                  <table key={i} style={{ width: "100%", fontSize: 11, borderCollapse: "collapse", marginBottom: 8 }}>
                    {t.columns && <thead><tr>{t.columns.map((c: string, j: number) => <th key={j} style={{ textAlign: "left", padding: "2px 6px", borderBottom: "1px solid #ddd" }}>{c}</th>)}</tr></thead>}
                    <tbody>{t.rows?.slice(0, 8).map((r: any[], j: number) => <tr key={j}>{r.map((c: any, k: number) => <td key={k} style={{ padding: "2px 6px", borderBottom: "1px solid #f0f0f0" }}>{String(c ?? "—")}</td>)}</tr>)}</tbody>
                  </table>
                ))}
                {interpretation ? (
                  <div style={{ fontSize: 13, lineHeight: 1.5, color: "#333" }}>{interpretation.summary}</div>
                ) : (
                  <button style={{ padding: "6px 14px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13 }} onClick={handleInterpret}>Explain Results</button>
                )}
              </div>
            ) : (
              <div style={{ fontSize: 12, color: "#888" }}>Select a method above to run analysis.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const S: Record<string, React.CSSProperties> = {
  container: { padding: 24, maxWidth: 960 },
  center: { display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#888" },
  header: { marginBottom: 16 },
  meta: { fontSize: 13, color: "#888" },
  tabRow: { display: "flex", gap: 4, marginBottom: 20 },
  wizard: { marginBottom: 20 },
  step: { marginBottom: 16 },
  stepLabel: { fontSize: 13, fontWeight: 600, color: "#555", marginBottom: 8 },
  goalRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 },
  varRow: { display: "flex", gap: 12 },
  select: { width: "100%", padding: "8px 10px", fontSize: 13, border: "1px solid #ddd", borderRadius: 6, background: "#fff", fontFamily: "inherit" },
  qbox: { display: "flex", gap: 8, marginBottom: 16 },
  input: { flex: 1, padding: "10px 14px", fontSize: 15, border: "1px solid #ddd", borderRadius: 8, resize: "none", fontFamily: "inherit" },
  askBtn: { padding: "10px 24px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: "pointer" },
  err: { padding: 12, background: "#fff0f0", border: "1px solid #fcc", borderRadius: 8, color: "#c00", marginBottom: 16 },
  secTitle: { fontSize: 14, fontWeight: 600, color: "#555", marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" },
  card: { padding: 12, border: "1px solid #e0e0e0", borderRadius: 8, cursor: "pointer", background: "#fff", marginBottom: 6 },
  cardSel: { border: "2px solid #1a73e8", background: "#f0f7ff" },
  panel: { padding: 16, border: "1px solid #e0e0e0", borderRadius: 8, background: "#fafafa" },
  reportBtn: { padding: "4px 12px", background: "#34a853", color: "#fff", border: "none", borderRadius: 4, fontSize: 12, cursor: "pointer" },
};

function tabStyle(active: boolean): React.CSSProperties {
  return {
    padding: "6px 16px", border: active ? "2px solid #1a73e8" : "2px solid #e0e0e0",
    borderRadius: 6, background: active ? "#f0f7ff" : "#fff", color: active ? "#1a73e8" : "#666",
    fontWeight: active ? 600 : 400, fontSize: 13, cursor: "pointer",
  };
}

function goalBtnStyle(active: boolean): React.CSSProperties {
  return {
    padding: "10px 12px", border: active ? "2px solid #1a73e8" : "1px solid #e0e0e0",
    borderRadius: 8, background: active ? "#f0f7ff" : "#fff", cursor: "pointer",
    textAlign: "left", fontFamily: "inherit",
  };
}
