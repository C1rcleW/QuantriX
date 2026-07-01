"""Homogeneity rule — checks equal variance assumption.

Required for t-test and ANOVA. Uses quick heuristics
(sd ratio across groups) instead of formal Levene's test.
"""

from __future__ import annotations

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

_HOMOGENEITY_METHODS: set[str] = {"independent_ttest", "oneway_anova"}
_MAX_SD_RATIO: float = 2.0  # Warn if max sd / min sd > 2


class HomogeneityRule(SafetyRule):
    rule_name = "homogeneity"
    rule_description = "Checks homogeneity of variance across groups."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        if method_name not in _HOMOGENEITY_METHODS:
            return []

        warnings: list[SafetyWarning] = []
        df = dataset.data
        if dv is None or not ivs or df is None:
            return warnings

        dv_col, iv_col = dv.name, ivs[0].name
        if dv_col not in df.columns or iv_col not in df.columns:
            return warnings

        # Compute SD per group
        groups = df.group_by(iv_col).agg(
            [
                pl.col(dv_col).std().alias("sd"),
                pl.col(dv_col).count().alias("n"),
            ]
        )

        sds = [row[1] for row in groups.rows() if row[1] is not None]
        if len(sds) < 2:
            return warnings

        max_sd, min_sd = max(sds), min(sds)
        # Special case: one group has SD=0 (all values identical)
        if min_sd == 0 and max_sd > 0:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="warning",
                    message=(
                        f"One group has zero variance (all values identical) "
                        f"while another has SD={max_sd:.1f}. "
                        "Homogeneity of variance is violated."
                    ),
                    suggestion="Consider Welch's t-test, which does not assume equal variances.",
                    variable_names=[dv_col, iv_col],
                )
            )
        elif min_sd > 0 and max_sd / min_sd > _MAX_SD_RATIO:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="warning",
                    message=(
                        f"Group standard deviations vary substantially "
                        f"(max/min = {max_sd / min_sd:.1f}, threshold={_MAX_SD_RATIO})."
                    ),
                    suggestion=(
                        "Consider Welch's t-test or Welch's ANOVA, "
                        "which do not assume equal variances."
                    ),
                    variable_names=[dv_col, iv_col],
                )
            )

        return warnings
