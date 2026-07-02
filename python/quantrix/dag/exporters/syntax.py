"""SPSS Syntax exporter."""

from __future__ import annotations

from quantrix.dag.graph import AnalysisDAG, NodeKind


def _get_dv_iv(params: dict[str, object]) -> tuple[str, str]:
    dv = str(params.get("dv", "outcome"))
    ivs = params.get("ivs")
    iv = str(ivs[0]) if isinstance(ivs, list) and ivs else str(params.get("iv", "predictor"))
    return dv, iv


def export_syntax(dag: AnalysisDAG, dataset_name: str = "data") -> str:
    lines = ["* SPSS Syntax - Quantrix.", f"GET FILE='{dataset_name}.sav'.", ""]
    for node in dag.topological_order():
        if node.kind == NodeKind.ANALYSIS:
            params = dict(node.parameters)
            dv, iv = _get_dv_iv(params)
            m = node.method
            if m == "independent_ttest":
                lines.append(f"T-TEST GROUPS={iv}(1 2) /VARIABLES={dv}.")
            elif m == "oneway_anova":
                lines.append(f"ONEWAY {dv} BY {iv} /STATISTICS DESCRIPTIVES.")
            elif m == "chi_square":
                lines.append(f"CROSSTABS /TABLES={iv} BY {dv} /STATISTICS=CHISQ.")
            elif m == "pearson_correlation":
                lines.append(f"CORRELATIONS /VARIABLES={dv} {iv}.")
            elif m == "linear_regression":
                lines.append(f"REGRESSION /DEPENDENT={dv} /METHOD=ENTER {iv}.")
            elif m in ("descriptive_statistics", "descriptives"):
                lines.append(f"DESCRIPTIVES VARIABLES={dv} /STATISTICS=MEAN STDDEV MIN MAX.")
            elif m == "frequency_analysis":
                lines.append(f"FREQUENCIES VARIABLES={dv} /ORDER=ANALYSIS.")
            else:
                lines.append(f"* {m}.")
            lines.append("")
    return "\n".join(lines)
