"""Type match rule — checks variable type × method compatibility.

This is the most fundamental safety check. Every statistical method
requires specific variable types. This rule catches type mismatches
before any computation happens.
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.safety.engine import SafetyRule, SafetyWarning

# Method → required dependent variable types
_METHOD_DV_TYPES: dict[str, set[str]] = {
    "descriptives": {"continuous"},
    "frequencies": {"nominal", "ordinal", "string"},
    "crosstab": {"nominal", "ordinal"},
    "independent_ttest": {"continuous"},
    "oneway_anova": {"continuous"},
    "mann_whitney": {"continuous", "ordinal"},
    "kruskal_wallis": {"continuous", "ordinal"},
    "chi_square": {"nominal", "ordinal"},
    "pearson_correlation": {"continuous"},
    "spearman_correlation": {"continuous", "ordinal"},
    "eta_squared": {"continuous"},
    "linear_regression": {"continuous"},
    "binary_logistic": {"nominal"},
    "multinomial_logistic": {"nominal"},
    "ordinal_logistic": {"ordinal"},
}

# Method → required independent variable types
_METHOD_IV_TYPES: dict[str, set[str]] = {
    "independent_ttest": {"nominal", "ordinal"},
    "oneway_anova": {"nominal", "ordinal"},
    "mann_whitney": {"nominal", "ordinal"},
    "kruskal_wallis": {"nominal", "ordinal"},
    "chi_square": {"nominal", "ordinal"},
    "pearson_correlation": {"continuous"},
    "spearman_correlation": {"continuous", "ordinal"},
    "eta_squared": {"nominal", "ordinal"},
    "linear_regression": {"continuous", "nominal", "ordinal"},
    "binary_logistic": {"continuous", "nominal", "ordinal"},
    "multinomial_logistic": {"continuous", "nominal", "ordinal"},
    "ordinal_logistic": {"continuous", "nominal", "ordinal"},
}


class TypeMatchRule(SafetyRule):
    rule_name = "type_match"
    rule_description = "Checks that variable types are compatible with the selected method."

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        warnings: list[SafetyWarning] = []

        allowed_dv = _METHOD_DV_TYPES.get(method_name)
        allowed_iv = _METHOD_IV_TYPES.get(method_name)

        # Unknown method → skip
        if allowed_dv is None and allowed_iv is None:
            return []

        # Check dependent variable
        if dv is not None and allowed_dv is not None and dv.variable_type.value not in allowed_dv:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="error",
                    message=(
                        f"Method '{method_name}' requires a dependent variable "
                        f"of type {sorted(allowed_dv)}, but '{dv.name}' is "
                        f"'{dv.variable_type.value}'."
                    ),
                    suggestion=(
                        f"Consider using a method compatible with "
                        f"'{dv.variable_type.value}' variables, or "
                        "transforming the variable."
                    ),
                    variable_names=[dv.name],
                )
            )

        # Check independent variables
        if ivs and allowed_iv is not None:
            for iv in ivs:
                if iv.variable_type.value not in allowed_iv:
                    warnings.append(
                        SafetyWarning(
                            rule_name=self.rule_name,
                            severity="error",
                            message=(
                                f"Method '{method_name}' expects independent variables "
                                f"of type {sorted(allowed_iv)}, but '{iv.name}' is "
                                f"'{iv.variable_type.value}'."
                            ),
                            suggestion=f"Consider reclassifying '{iv.name}' or choosing a different method.",
                            variable_names=[iv.name],
                        )
                    )

        # Special case: binary logistic requires exactly 2 categories in DV
        if method_name == "binary_logistic" and dv is not None and dv.n_unique is not None and dv.n_unique != 2:
            warnings.append(
                SafetyWarning(
                    rule_name=self.rule_name,
                    severity="error",
                    message=(
                        f"Binary logistic regression requires exactly 2 categories "
                        f"in the dependent variable, but '{dv.name}' has "
                        f"{dv.n_unique} unique values."
                    ),
                    suggestion="Recode the dependent variable to exactly 2 categories.",
                    variable_names=[dv.name],
                )
            )

        return warnings
