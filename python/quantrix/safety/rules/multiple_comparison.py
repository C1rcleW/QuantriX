"""Multiple comparison rule — reminds about inflated Type I error.

Triggers when multiple independent variables are being tested
or when the method implies many pairwise comparisons.
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

# Methods where multiple comparisons are a concern
_MULTI_COMPARE_METHODS: set[str] = {
    "oneway_anova",
    "kruskal_wallis",
    "linear_regression",
    "multinomial_logistic",
}

# Methods that produce group comparison results
_GROUP_COMPARE_METHODS: set[str] = {
    "crosstab",
}


class MultipleComparisonRule(SafetyRule):
    rule_name = "multiple_comparison"
    rule_description = "Reminds about inflated Type I error with multiple tests."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        warnings: list[SafetyWarning] = []

        # Multiple independent variables in regression → remind
        if method_name == "linear_regression" and len(ivs) > 1:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="info",
                    message=(
                        f"Testing {len(ivs)} predictors simultaneously. "
                        "Each coefficient test carries its own Type I error risk."
                    ),
                    suggestion="Consider reporting adjusted R² instead of individual p-values, or use a hierarchical entry method.",
                    variable_names=[iv.name for iv in ivs],
                )
            )

        # Multi-group test → suggest post-hoc
        if method_name in ("oneway_anova", "kruskal_wallis") and ivs and ivs[0].n_unique and ivs[0].n_unique > 2:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="info",
                    message=(
                        f"With {ivs[0].n_unique} groups, pairwise comparisons "
                        "require correction for multiple testing."
                    ),
                    suggestion=(
                        "Use Tukey's HSD (ANOVA) or Dunn's test (Kruskal-Wallis) "
                        "with Bonferroni correction for post-hoc comparisons."
                    ),
                    variable_names=[ivs[0].name],
                )
            )

        # Multiple IVs in crosstab → remind
        if method_name == "crosstab" and len(ivs) > 1:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="info",
                    message=(
                        f"Testing associations with {len(ivs)} variables "
                        "inflates familywise error rate."
                    ),
                    suggestion="Apply Bonferroni correction: divide α by number of tests.",
                )
            )

        return warnings
