"""Outlier rule — IQR-based univariate outlier detection.

Flags potential outliers in the dependent variable.
Does not remove them — only warns the researcher.
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

_IQR_MULTIPLIER: float = 1.5
_MIN_OUTLIER_PCT: float = 5.0  # Only warn if >5% of values are outliers


class OutlierRule(SafetyRule):
    rule_name = "outliers"
    rule_description = "Detects univariate outliers using the IQR method."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        warnings: list[SafetyWarning] = []
        df = dataset.data
        if dv is None or df is None or dv.name not in df.columns:
            return warnings

        col = df[dv.name].drop_nulls()
        if len(col) < 4:
            return warnings

        q1 = col.quantile(0.25)
        q3 = col.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            # All values identical or nearly so — flag anything different
            mode_val = col.mode().item() if len(col.mode()) > 0 else col[0]
            outlier_mask = col != mode_val
            n_outliers = int(outlier_mask.sum())
            if n_outliers > 0:
                dv.outlier_count = n_outliers
                outlier_pct = n_outliers / len(col) * 100
                if outlier_pct > _MIN_OUTLIER_PCT:
                    warnings.append(SafetyWarning(
                        rule_name=self.rule_name,
                        severity="warning",
                        message=(
                            f"'{dv.name}' has {n_outliers} value(s) differing "
                            f"from the majority ({mode_val}). IQR is zero, "
                            f"so these are flagged as potential outliers."
                        ),
                        suggestion="Investigate these cases.",
                        variable_names=[dv.name],
                    ))
            return warnings

        lower = q1 - _IQR_MULTIPLIER * iqr
        upper = q3 + _IQR_MULTIPLIER * iqr

        outlier_mask = (col < lower) | (col > upper)
        n_outliers = int(outlier_mask.sum())
        outlier_pct = n_outliers / len(col) * 100

        if n_outliers > 0:
            dv.outlier_count = n_outliers

        if outlier_pct > _MIN_OUTLIER_PCT:
            warnings.append(SafetyWarning(
                rule_name=self.rule_name,
                severity="warning",
                message=(
                    f"'{dv.name}' has {n_outliers} potential outlier(s) "
                    f"({outlier_pct:.1f}% of valid values). "
                    f"Range: [{lower:.2f}, {upper:.2f}]."
                ),
                suggestion=(
                    "Investigate these cases. Consider: (1) verifying data entry, "
                    "(2) winsorizing, (3) using robust methods, or "
                    "(4) reporting results with and without outliers."
                ),
                variable_names=[dv.name],
            ))
        elif n_outliers > 0:
            warnings.append(SafetyWarning(
                rule_name=self.rule_name,
                severity="info",
                message=(
                    f"'{dv.name}' has {n_outliers} potential outlier(s) "
                    f"({outlier_pct:.1f}% of valid values)."
                ),
            ))

        return warnings
