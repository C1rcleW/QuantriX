"""Statistical method decision tree.

Maps research question types + variable characteristics to appropriate
statistical methods. This is the rule engine that guarantees statistical
correctness — LLM is only used for question parsing, not method selection.

Design principle: every path through this tree must be defensible from
a statistical methodology standpoint. When in doubt, we prefer the more
conservative (nonparametric) recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType

# ── Question types the researcher might have ───────────────────────────────


class ResearchGoal:
    """What the researcher wants to know."""

    DESCRIBE = "describe"  # Summarise / visualise a variable
    COMPARE_GROUPS = "compare"  # Difference between groups
    ASSOCIATION = "associate"  # Relationship between variables
    PREDICT = "predict"  # One variable predicts another


# ── Method recommendations ──────────────────────────────────────────────────


@dataclass
class MethodCandidate:
    """A single statistical method recommendation."""

    method_name: str  # e.g., "independent_samples_ttest"
    display_name: str  # e.g., "Independent Samples t-test"
    method_family: str  # "descriptive", "comparison", "correlation", "regression"
    confidence: float  # 0.0–1.0, how well this method fits
    reason: str  # Why this method is recommended
    required_variables: dict[str, int] = field(default_factory=dict)
    # e.g., {"dependent": 1, "independent": 1}
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)


# ── The decision tree ──────────────────────────────────────────────────────


class DecisionTree:
    """Maps research goals + variable types → ranked method recommendations.

    Usage:
        tree = DecisionTree()
        candidates = tree.recommend(
            goal=ResearchGoal.COMPARE_GROUPS,
            dependent=income_var,
            independents=[gender_var],
        )
    """

    def recommend(
        self,
        goal: str,
        dependent: VariableMetadata | None = None,
        independents: list[VariableMetadata] | None = None,
    ) -> list[MethodCandidate]:
        """Generate ranked method recommendations.

        Args:
            goal: One of ResearchGoal values.
            dependent: The outcome / dependent variable (optional for descriptive).
            independents: Predictor / grouping variables.

        Returns:
            Ranked list of method candidates (best fit first).
        """
        if goal == ResearchGoal.DESCRIBE:
            return self._recommend_descriptive(dependent, independents or [])
        elif goal == ResearchGoal.COMPARE_GROUPS:
            return self._recommend_comparison(dependent, independents or [])
        elif goal == ResearchGoal.ASSOCIATION:
            return self._recommend_association(dependent, independents or [])
        elif goal == ResearchGoal.PREDICT:
            return self._recommend_prediction(dependent, independents or [])
        else:
            return []

    # ── Descriptive ────────────────────────────────────────────────────

    def _recommend_descriptive(
        self,
        dependent: VariableMetadata | None,
        independents: list[VariableMetadata],
    ) -> list[MethodCandidate]:
        candidates: list[MethodCandidate] = []

        if dependent is None:
            return candidates

        if dependent.is_continuous:
            candidates.append(
                MethodCandidate(
                    method_name="descriptives",
                    display_name="Descriptive Statistics",
                    method_family="descriptive",
                    confidence=1.0,
                    reason="Continuous variables are best summarised with mean, SD, and distribution plots.",
                    assumptions=["No assumptions required for description."],
                )
            )
        elif dependent.is_categorical:
            candidates.append(
                MethodCandidate(
                    method_name="frequencies",
                    display_name="Frequency Analysis",
                    method_family="descriptive",
                    confidence=1.0,
                    reason="Categorical variables are best summarised with frequencies and percentages.",
                    assumptions=["No assumptions required."],
                )
            )

        # If we have a categorical independent, add crosstab
        if independents and all(iv.is_categorical for iv in independents):
            candidates.append(
                MethodCandidate(
                    method_name="crosstab",
                    display_name="Crosstabulation",
                    method_family="descriptive",
                    confidence=0.9,
                    reason=(
                        "Crosstabulation shows how the dependent variable distributes "
                        "across categories. Not implemented in this build; frequency "
                        "analysis covers the marginal distribution."
                    ),
                    assumptions=[
                        "Expected frequencies should be ≥ 5 in ≥ 80% of cells for chi-square."
                    ],
                    alternatives=["Frequency analysis (executable)", "Chi-square test of independence"],
                )
            )

        return candidates

    # ── Group comparison ───────────────────────────────────────────────

    def _recommend_comparison(
        self,
        dependent: VariableMetadata | None,
        independents: list[VariableMetadata],
    ) -> list[MethodCandidate]:
        if dependent is None or not independents:
            return []
        if (
            not independents[0].is_categorical
            or independents[0].variable_type == VariableType.STRING
        ):
            return []

        candidates: list[MethodCandidate] = []
        n_groups = independents[0].n_unique if independents[0].n_unique else 2

        # Continuous dependent
        if dependent.is_continuous:
            if n_groups == 2:
                candidates.append(
                    MethodCandidate(
                        method_name="independent_ttest",
                        display_name="Independent Samples t-test",
                        method_family="comparison",
                        confidence=0.95,
                        reason=f"Comparing a continuous outcome between {n_groups} groups.",
                        assumptions=[
                            "Normality: dependent variable should be approximately normal in each group.",
                            "Homogeneity of variance: Levene's test p > .05.",
                            "Independence: observations must be independent.",
                        ],
                        alternatives=[
                            "Mann-Whitney U test (nonparametric)",
                            "Welch's t-test (unequal variances)",
                        ],
                    )
                )
                candidates.append(
                    MethodCandidate(
                        method_name="mann_whitney",
                        display_name="Mann-Whitney U Test",
                        method_family="comparison",
                        confidence=0.7,
                        reason="Nonparametric alternative if normality is violated.",
                        assumptions=[
                            "Independence of observations.",
                            "Ordinal or continuous dependent.",
                        ],
                        alternatives=["Independent samples t-test"],
                    )
                )
            else:
                candidates.append(
                    MethodCandidate(
                        method_name="oneway_anova",
                        display_name="One-Way ANOVA",
                        method_family="comparison",
                        confidence=0.95,
                        reason=f"Comparing a continuous outcome across {n_groups} groups.",
                        assumptions=[
                            "Normality: dependent variable should be approximately normal in each group.",
                            "Homogeneity of variance: Levene's test p > .05.",
                            "Independence of observations.",
                        ],
                        alternatives=[
                            "Kruskal-Wallis test (nonparametric)",
                            "Welch's ANOVA (unequal variances)",
                        ],
                    )
                )
                candidates.append(
                    MethodCandidate(
                        method_name="kruskal_wallis",
                        display_name="Kruskal-Wallis H Test",
                        method_family="comparison",
                        confidence=0.7,
                        reason="Nonparametric alternative if normality is violated.",
                        assumptions=["Independence of observations."],
                        alternatives=["One-way ANOVA"],
                    )
                )

        # Ordinal dependent
        elif dependent.variable_type == VariableType.ORDINAL:
            if n_groups == 2:
                candidates.append(
                    MethodCandidate(
                        method_name="mann_whitney",
                        display_name="Mann-Whitney U Test",
                        method_family="comparison",
                        confidence=0.95,
                        reason="Appropriate for comparing ordinal outcomes between 2 groups.",
                        assumptions=[
                            "Independence of observations.",
                            "Similar distribution shape across groups.",
                        ],
                    )
                )
            else:
                candidates.append(
                    MethodCandidate(
                        method_name="kruskal_wallis",
                        display_name="Kruskal-Wallis H Test",
                        method_family="comparison",
                        confidence=0.95,
                        reason="Appropriate for comparing ordinal outcomes across multiple groups.",
                        assumptions=["Independence of observations."],
                    )
                )

        # Nominal dependent
        elif dependent.variable_type == VariableType.NOMINAL:
            candidates.append(
                MethodCandidate(
                    method_name="chi_square",
                    display_name="Chi-Square Test of Independence",
                    method_family="comparison",
                    confidence=0.95,
                    reason="Compares categorical distributions between groups.",
                    assumptions=[
                        "Expected frequency ≥ 5 in ≥ 80% of cells.",
                        "Observations are independent.",
                    ],
                    alternatives=["Fisher's Exact Test (small samples)"],
                )
            )

        return candidates

    # ── Association ────────────────────────────────────────────────────

    def _recommend_association(
        self,
        dependent: VariableMetadata | None,
        independents: list[VariableMetadata],
    ) -> list[MethodCandidate]:
        if dependent is None or not independents:
            return []

        candidates: list[MethodCandidate] = []
        iv = independents[0]
        if iv.variable_type == VariableType.STRING:
            return []

        # Continuous × Continuous → Pearson + Spearman
        if dependent.is_continuous and iv.is_continuous:
            candidates.append(
                MethodCandidate(
                    method_name="pearson_correlation",
                    display_name="Pearson Correlation",
                    method_family="correlation",
                    confidence=0.95,
                    reason="Measures linear association between two continuous variables.",
                    assumptions=[
                        "Both variables should be approximately normally distributed.",
                        "Linear relationship (check scatterplot).",
                        "No significant outliers.",
                    ],
                    alternatives=["Spearman's rank correlation (nonparametric)"],
                )
            )
            candidates.append(
                MethodCandidate(
                    method_name="spearman_correlation",
                    display_name="Spearman Rank Correlation",
                    method_family="correlation",
                    confidence=0.7,
                    reason="Nonparametric alternative; also detects monotonic (not just linear) relationships.",
                    assumptions=["Monotonic relationship."],
                )
            )
            return candidates

        # Continuous outcome × categorical predictor → executable ANOVA/t-test
        if dependent.is_continuous and iv.is_categorical:
            n_groups = iv.n_unique or 2
            if n_groups == 2:
                candidates.append(
                    MethodCandidate(
                        method_name="independent_ttest",
                        display_name="Independent Samples t-test",
                        method_family="comparison",
                        confidence=0.85,
                        reason=(
                            "Compares the continuous outcome across the two categories. "
                            "This is the executable form of the continuous–categorical "
                            "association in the current build."
                        ),
                        assumptions=[
                            "Normality within each group (approximately).",
                            "Homogeneity of variance.",
                            "Independence of observations.",
                        ],
                        alternatives=[
                            "Mann-Whitney U (nonparametric)",
                            "Eta-squared (not yet implemented separately)",
                        ],
                    )
                )
            else:
                candidates.append(
                    MethodCandidate(
                        method_name="oneway_anova",
                        display_name="One-Way ANOVA",
                        method_family="comparison",
                        confidence=0.85,
                        reason=(
                            "Tests whether the continuous outcome differs across the "
                            f"{n_groups} categories. This is the executable form of the "
                            "continuous–categorical association in the current build."
                        ),
                        assumptions=[
                            "Normality within each group (approximately).",
                            "Homogeneity of variance.",
                            "Independence of observations.",
                        ],
                        alternatives=[
                            "Kruskal-Wallis test (nonparametric)",
                            "Eta-squared (not yet implemented separately)",
                        ],
                    )
                )

            candidates.append(
                MethodCandidate(
                    method_name="eta_squared",
                    display_name="Eta-Squared (η²)",
                    method_family="correlation",
                    confidence=0.75,
                    reason=(
                        "Quantifies association strength between a continuous and "
                        "categorical variable. Not implemented separately in this build; "
                        "ANOVA/t-test provides the corresponding significance test."
                    ),
                    assumptions=["Independence of observations."],
                    alternatives=["One-way ANOVA / independent t-test (executable)"],
                )
            )
            return candidates

        # Ordinal outcome × continuous predictor → Spearman
        if dependent.variable_type == VariableType.ORDINAL and iv.is_continuous:
            candidates.append(
                MethodCandidate(
                    method_name="spearman_correlation",
                    display_name="Spearman Rank Correlation",
                    method_family="correlation",
                    confidence=0.9,
                    reason="Appropriate for an ordinal outcome and a continuous predictor.",
                    assumptions=["Monotonic relationship."],
                )
            )
            return candidates

        # Categorical outcome × categorical predictor → ordinal-aware options
        if dependent.is_categorical and iv.is_categorical:
            if (
                dependent.variable_type == VariableType.ORDINAL
                and iv.variable_type == VariableType.ORDINAL
            ):
                candidates.append(
                    MethodCandidate(
                        method_name="spearman_correlation",
                        display_name="Spearman Rank Correlation",
                        method_family="correlation",
                        confidence=0.9,
                        reason="Appropriate for two ordinal variables.",
                        assumptions=["Monotonic relationship."],
                    )
                )
            elif (
                dependent.variable_type == VariableType.ORDINAL
                and iv.variable_type == VariableType.NOMINAL
            ):
                candidates.append(
                    MethodCandidate(
                        method_name="kruskal_wallis",
                        display_name="Kruskal-Wallis H Test",
                        method_family="comparison",
                        confidence=0.9,
                        reason="Compares an ordinal outcome across nominal groups.",
                        assumptions=["Independence of observations."],
                    )
                )
            candidates.append(
                MethodCandidate(
                    method_name="chi_square",
                    display_name="Chi-Square Test of Independence",
                    method_family="correlation",
                    confidence=0.8,
                    reason="Tests association between two categorical variables.",
                    assumptions=[
                        "Expected frequency ≥ 5 in ≥ 80% of cells.",
                        "Observations are independent.",
                    ],
                )
            )
            return candidates

        # Categorical outcome × continuous predictor → logistic regression family
        if dependent.is_categorical and iv.is_continuous:
            binary = dependent.n_unique == 2
            method_name = "binary_logistic" if binary else "multinomial_logistic"
            display_name = (
                "Binary Logistic Regression"
                if binary
                else "Multinomial Logistic Regression"
            )
            candidates.append(
                MethodCandidate(
                    method_name=method_name,
                    display_name=display_name,
                    method_family="regression",
                    confidence=0.8,
                    reason=(
                        "Association between a categorical outcome and a continuous "
                        "predictor is usually modeled with logistic regression. Not "
                        "implemented in this build; shown as the statistically "
                        "appropriate target method."
                    ),
                    assumptions=[
                        "Observations are independent.",
                        "No severe multicollinearity.",
                    ],
                    alternatives=[
                        "Chi-square after categorizing the continuous predictor (not recommended)",
                        "Point-biserial correlation (binary outcome only; not implemented)",
                    ],
                )
            )
            return candidates

        return candidates

    # ── Prediction ─────────────────────────────────────────────────────

    def _recommend_prediction(
        self,
        dependent: VariableMetadata | None,
        independents: list[VariableMetadata],
    ) -> list[MethodCandidate]:
        if dependent is None or not independents:
            return []

        candidates: list[MethodCandidate] = []

        # Continuous DV → Linear regression
        if dependent.is_continuous:
            if any(iv.variable_type == VariableType.STRING for iv in independents):
                return []
            candidates.append(
                MethodCandidate(
                    method_name="linear_regression",
                    display_name="Linear Regression",
                    method_family="regression",
                    confidence=0.95,
                    reason="Models how independent variables predict a continuous outcome.",
                    assumptions=[
                        "Linearity: relationship between predictors and outcome is linear.",
                        "Independence of residuals.",
                        "Homoscedasticity: constant variance of residuals.",
                        "Normality of residuals.",
                        "No severe multicollinearity (VIF < 10).",
                    ],
                    alternatives=["Robust regression", "Quantile regression"],
                )
            )

        # Binary DV → Logistic regression
        elif dependent.variable_type == VariableType.NOMINAL and (
            dependent.n_unique is not None and dependent.n_unique == 2
        ):
            candidates.append(
                MethodCandidate(
                    method_name="binary_logistic",
                    display_name="Binary Logistic Regression",
                    method_family="regression",
                    confidence=0.95,
                    reason=(
                        "Models probability of a binary outcome based on predictors. "
                        "Not implemented in this build; shown as the statistically "
                        "appropriate target method."
                    ),
                    assumptions=[
                        "Binary dependent variable (0/1).",
                        "Linearity in the logit: continuous predictors linearly related to log-odds.",
                        "No severe multicollinearity.",
                        "Independence of observations.",
                    ],
                    alternatives=[
                        "Chi-square test of independence (association only)",
                        "Recode the outcome or choose a continuous outcome",
                    ],
                )
            )

        # Multi-category DV → Multinomial logistic
        elif dependent.variable_type == VariableType.NOMINAL:
            candidates.append(
                MethodCandidate(
                    method_name="multinomial_logistic",
                    display_name="Multinomial Logistic Regression",
                    method_family="regression",
                    confidence=0.85,
                    reason=(
                        "Models a nominal outcome with more than 2 categories. "
                        "Not implemented in this build; shown as the statistically "
                        "appropriate target method."
                    ),
                    assumptions=[
                        "Independence of irrelevant alternatives (IIA).",
                        "No severe multicollinearity.",
                    ],
                    alternatives=[
                        "Chi-square test of independence (association only)",
                        "Collapse categories and use a binary method when available",
                    ],
                )
            )

        # Ordinal DV → Ordinal logistic
        elif dependent.variable_type == VariableType.ORDINAL:
            candidates.append(
                MethodCandidate(
                    method_name="ordinal_logistic",
                    display_name="Ordinal Logistic Regression",
                    method_family="regression",
                    confidence=0.9,
                    reason=(
                        "Models an ordered categorical outcome. Not implemented in this "
                        "build; shown as the statistically appropriate target method."
                    ),
                    assumptions=[
                        "Proportional odds assumption.",
                        "No severe multicollinearity.",
                    ],
                    alternatives=[
                        "Spearman correlation / Kruskal-Wallis (exploratory association)",
                        "Use an ordinal outcome model when it becomes available",
                    ],
                )
            )

        return candidates
