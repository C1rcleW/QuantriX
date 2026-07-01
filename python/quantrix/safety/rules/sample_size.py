"""Sample size rule — checks minimum N requirements.

Different methods have different sample size requirements.
This rule checks the basics and warns when N is marginal.
"""

from __future__ import annotations

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

# Minimum sample sizes per method
_MIN_N: dict[str, int] = {
    "independent_ttest": 6,  # 3 per group minimum
    "oneway_anova": 15,  # 5 per group × 3 groups
    "mann_whitney": 8,  # 4 per group
    "chi_square": 10,
    "pearson_correlation": 20,
    "spearman_correlation": 10,
    "linear_regression": 30,  # 10 per predictor minimum
    "binary_logistic": 30,
}

# Per-group minimum for group comparisons
_MIN_PER_GROUP: int = 3


class SampleSizeRule(SafetyRule):
    rule_name = "sample_size"
    rule_description = "Checks total N and per-group N adequacy."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        warnings: list[SafetyWarning] = []
        df = dataset.data
        if df is None:
            return warnings

        n_total = dataset.n_rows
        min_n = _MIN_N.get(method_name)

        if min_n is not None and n_total < min_n:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="warning",
                    message=(
                        f"Total sample size (N={n_total}) is below the recommended "
                        f"minimum of {min_n} for {method_name}."
                    ),
                    suggestion="Results may lack statistical power. Consider collecting more data or using a nonparametric alternative.",
                )
            )

        # Per-group check for group comparison methods
        if method_name in ("independent_ttest", "oneway_anova", "mann_whitney", "kruskal_wallis"):
            if ivs and df is not None:
                group_col = ivs[0].name
                if group_col in df.columns:
                    counts = df[group_col].value_counts()
                    small_groups = [
                        (row[0], row[1]) for row in counts.rows() if row[1] < _MIN_PER_GROUP
                    ]
                    for group_val, count in small_groups:
                        warnings.append(
                            SafetyWarning(
                                rule_name=self.rule_name,
                                severity="error",
                                message=(
                                    f"Group '{group_val}' has only {count} observation(s), "
                                    f"below the minimum of {_MIN_PER_GROUP}."
                                ),
                                suggestion="Consider merging small groups or using a nonparametric test.",
                                variable_names=[group_col],
                            )
                        )

        # Chi-square expected frequency check
        if method_name == "chi_square" and dv is not None and ivs and df is not None:
            if dv.name in df.columns and ivs[0].name in df.columns:
                # Quick heuristic: if any cell in the crosstab has <5, warn
                crosstab = df.group_by([ivs[0].name, dv.name]).len()
                small_cells = crosstab.filter(pl.col("len") < 5)
                if small_cells.height > 0:
                    total_cells = crosstab.height
                    small_pct = small_cells.height / total_cells * 100
                    if small_pct > 20:
                        warnings.append(
                            SafetyWarning(
                                rule_name=self.rule_name,
                                severity="warning",
                                message=(
                                    f"{small_cells.height}/{total_cells} cells "
                                    f"({small_pct:.0f}%) have expected frequency < 5."
                                ),
                                suggestion="Consider using Fisher's Exact Test or collapsing categories.",
                                variable_names=[dv.name, ivs[0].name],
                            )
                        )

        return warnings
