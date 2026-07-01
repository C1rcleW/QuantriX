"""Normality rule — checks distribution shape for parametric tests.

Uses skewness/kurtosis thresholds (fast) instead of formal
Shapiro-Wilk tests (which require scipy and are slow on large N).
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

# Methods that require normality of the dependent variable
_NORMALITY_METHODS: set[str] = {
    "independent_ttest", "oneway_anova", "pearson_correlation",
    "linear_regression",
}

_SKEWNESS_THRESHOLD: float = 2.0
_KURTOSIS_THRESHOLD: float = 3.0


class NormalityRule(SafetyRule):
    rule_name = "normality"
    rule_description = "Checks normality assumption via skewness/kurtosis heuristics."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        if method_name not in _NORMALITY_METHODS:
            return []

        warnings: list[SafetyWarning] = []
        df = dataset.data
        if dv is None or df is None or dv.name not in df.columns:
            return warnings

        col = df[dv.name].drop_nulls()
        if len(col) < 3:
            return warnings

        # Calculate skewness
        mean = col.mean()
        std = col.std()
        if std and std > 0:
            skewness = ((col - mean) ** 3).mean() / (std ** 3)
        else:
            return warnings

        # Calculate excess kurtosis
        kurtosis = ((col - mean) ** 4).mean() / (std ** 4) - 3

        var_names = [dv.name]

        if abs(skewness) > _SKEWNESS_THRESHOLD:
            direction = "positively" if skewness > 0 else "negatively"
            warnings.append(SafetyWarning(
                rule_name=self.rule_name,
                severity="warning",
                message=(
                    f"'{dv.name}' is {direction} skewed "
                    f"(skewness={skewness:.2f}, threshold={_SKEWNESS_THRESHOLD})."
                ),
                suggestion=(
                    "Consider a log/square-root transformation, "
                    "or use a nonparametric alternative (e.g., Mann-Whitney, "
                    "Spearman correlation, or robust regression)."
                ),
                variable_names=var_names,
            ))

        if abs(kurtosis) > _KURTOSIS_THRESHOLD:
            warnings.append(SafetyWarning(
                rule_name=self.rule_name,
                severity="warning",
                message=(
                    f"'{dv.name}' has high kurtosis "
                    f"(excess kurtosis={kurtosis:.2f})."
                ),
                suggestion="Heavy tails may inflate Type I error. Consider robust methods.",
                variable_names=var_names,
            ))

        # Update variable metadata with computed values
        dv.skewness = round(float(skewness), 3)
        dv.kurtosis = round(float(kurtosis), 3)

        return warnings
