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
                    reason="Crosstabulation shows how the dependent variable distributes across categories.",
                    assumptions=[
                        "Expected frequencies should be ≥ 5 in ≥ 80% of cells for chi-square."
                    ],
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

        # Continuous × Continuous → Pearson
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

        # Ordinal × Ordinal or Ordinal × Continuous → Spearman
        elif (
            dependent.variable_type == VariableType.ORDINAL
            or iv.variable_type == VariableType.ORDINAL
        ):
            candidates.append(
                MethodCandidate(
                    method_name="spearman_correlation",
                    display_name="Spearman Rank Correlation",
                    method_family="correlation",
                    confidence=0.95,
                    reason="Appropriate when at least one variable is ordinal.",
                    assumptions=["Monotonic relationship."],
                )
            )

        # Nominal × Nominal → Chi-square
        elif dependent.is_categorical and iv.is_categorical:
            candidates.append(
                MethodCandidate(
                    method_name="chi_square",
                    display_name="Chi-Square Test of Independence",
                    method_family="correlation",
                    confidence=0.95,
                    reason="Tests association between two categorical variables.",
                    assumptions=[
                        "Expected frequency ≥ 5 in ≥ 80% of cells.",
                        "Observations are independent.",
                    ],
                )
            )

        # Nominal × Continuous → Point-biserial or eta-squared
        elif dependent.is_continuous and iv.is_categorical:
            candidates.append(
                MethodCandidate(
                    method_name="eta_squared",
                    display_name="Eta-Squared (η²)",
                    method_family="correlation",
                    confidence=0.8,
                    reason="Measures association strength between a continuous and categorical variable.",
                    assumptions=["Independence of observations."],
                )
            )

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
                    reason="Models probability of a binary outcome based on predictors.",
                    assumptions=[
                        "Binary dependent variable (0/1).",
                        "Linearity in the logit: continuous predictors linearly related to log-odds.",
                        "No severe multicollinearity.",
                        "Independence of observations.",
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
                    reason="Models a nominal outcome with more than 2 categories.",
                    assumptions=[
                        "Independence of irrelevant alternatives (IIA).",
                        "No severe multicollinearity.",
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
                    reason="Models an ordered categorical outcome.",
                    assumptions=[
                        "Proportional odds assumption.",
                        "No severe multicollinearity.",
                    ],
                )
            )

        return candidates
