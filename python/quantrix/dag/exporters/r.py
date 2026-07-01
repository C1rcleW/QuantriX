"""R code exporter."""

from __future__ import annotations

from quantrix.dag.graph import AnalysisDAG, NodeKind


def export_r(dag: AnalysisDAG, dataset_name: str = "data") -> str:
    lines = [
        "# Reproducible R script — Quantrix",
        "library(haven)",
        "",
        f"# df <- read_sav('{dataset_name}.sav')",
        f"# df <- read_csv('{dataset_name}.csv')",
        "",
    ]
    for node in dag.topological_order():
        if node.kind == NodeKind.ANALYSIS:
            params = node.parameters
            dv = params.get("dv", "outcome")
            iv = params.get("iv", "predictor")
            m = node.method

            if m == "independent_ttest":
                lines.append(f"result <- t.test(df${dv} ~ df${iv})")
                lines.append("print(result)")
            elif m == "oneway_anova":
                lines.append(f"result <- aov({dv} ~ factor({iv}), data=df)")
                lines.append("print(summary(result))")
            elif m == "pearson_correlation":
                lines.append(f"result <- cor.test(df${dv}, df${iv}, method='pearson')")
                lines.append("print(result)")
            elif m == "chi_square":
                lines.append(f"result <- chisq.test(table(df${iv}, df${dv}))")
                lines.append("print(result)")
            elif m == "linear_regression":
                lines.append(f"model <- lm({dv} ~ {iv}, data=df)")
                lines.append("print(summary(model))")
            else:
                lines.append(f"# {m}")
            lines.append("")
    return "\n".join(lines)
