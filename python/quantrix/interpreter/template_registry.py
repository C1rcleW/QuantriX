"""Result interpretation templates.

Each template maps a method name to a natural-language interpretation
format. Templates use {key} placeholders filled from AnalysisResult.

Phase 4 uses pure template substitution (no LLM required).
Phase 6 will add optional LLM polish.
"""

from __future__ import annotations

# ── Template registry ──────────────────────────────────────────────────

_TEMPLATES: dict[str, str] = {}
_ALIASES: dict[str, str] = {}


def register(method_name: str, template: str) -> None:
    _TEMPLATES[method_name] = template


def register_alias(method_name: str, target: str) -> None:
    _ALIASES[method_name] = target


def get(method_name: str) -> str | None:
    if method_name in _TEMPLATES:
        return _TEMPLATES[method_name]
    if method_name in _ALIASES:
        return _TEMPLATES.get(_ALIASES[method_name])
    return None


# ── Descriptive statistics ─────────────────────────────────────────────


register(
    "descriptive_statistics",
    """\
## Descriptive Statistics for **{dv_label}**

{dv_label} was measured on {n} observations (valid: {n_valid}, missing: {missing_count}, {missing_pct:.1f}%).

The average {dv_label} was **{mean:.2f}** (SD = {std_dev:.2f}), \
ranging from {min_val:.2f} to {max_val:.2f}.

{skewness_text}\
""",
)

register(
    "frequency_analysis",
    """\
## Frequency Analysis for **{dv_label}**

{category_summary}

A total of {n} responses were recorded across {n_categories} categories.
The most common category was **"{mode_category}"** ({mode_count} responses, {mode_pct:.1f}%).
""",
)

# ── Group comparison ───────────────────────────────────────────────────


register(
    "independent_ttest",
    """\
## Independent Samples t-test: {dv_label} by {iv_label}

An independent samples t-test was conducted to compare {dv_label} \
between {group_labels}.

- **{group_labels[0]}**: M = {means[0]:.2f}, SD = {sds[0]:.2f}, n = {ns[0]}
- **{group_labels[1]}**: M = {means[1]:.2f}, SD = {sds[1]:.2f}, n = {ns[1]}

{sig_text}
{effect_size_text}
""",
)

register(
    "oneway_anova",
    """\
## One-Way ANOVA: {dv_label} by {iv_label}

A one-way ANOVA was conducted to compare {dv_label} across \
{n_groups} groups of {iv_label}.

{sig_text}

{group_table}

{effect_size_text}
{posthoc_note}
""",
)

register(
    "mann_whitney",
    """\
## Mann-Whitney U Test: {dv_label} by {iv_label}

A Mann-Whitney U test (nonparametric alternative to the independent \
t-test) was conducted to compare {dv_label} between {group_labels}.

{sig_text}
{effect_size_text}
""",
)

register(
    "kruskal_wallis",
    """\
## Kruskal-Wallis H Test: {dv_label} by {iv_label}

A Kruskal-Wallis H test (nonparametric alternative to one-way ANOVA) \
was conducted to compare {dv_label} across {n_groups} groups.

{sig_text}
{effect_size_text}
""",
)

# ── Association ────────────────────────────────────────────────────────


register(
    "pearson_correlation",
    """\
## Pearson Correlation: {dv_label} and {iv_label}

A Pearson correlation was computed to assess the linear relationship \
between {dv_label} and {iv_label}.

There was a **{strength} {direction}** correlation between the two \
variables, r({df}) = {r:.3f}, {sig_text}.

This indicates that {interpretation}.
""",
)

register(
    "spearman_correlation",
    """\
## Spearman Rank Correlation: {dv_label} and {iv_label}

A Spearman rank-order correlation was computed to assess the monotonic \
relationship between {dv_label} and {iv_label}.

There was a **{strength} {direction}** correlation, \
ρ({n}) = {rho:.3f}, {sig_text}.

{note}
""",
)

register(
    "chi_square",
    """\
## Chi-Square Test of Independence: {dv_label} × {iv_label}

A chi-square test of independence was performed to examine the \
relationship between {dv_label} and {iv_label}.

{sig_text}

{cell_note}
{effect_size_text}
""",
)

# ── Prediction ─────────────────────────────────────────────────────────


register(
    "linear_regression",
    """\
## Linear Regression: Predicting {dv_label}

A linear regression was conducted to predict {dv_label} from \
{predictor_list}.

The overall model was {sig_text}, \
R² = {r_squared:.3f} (adjusted R² = {r_squared_adj:.3f}), \
F({df_model}, {df_residual}) = {f_stat:.2f}.

The model explains {r_squared_pct:.1f}% of the variance in {dv_label}.

{coefficient_table}
""",
)


# ── Helpers for template filling ───────────────────────────────────────


def interpret_p_value(p: float, alpha: float = 0.05) -> str:
    """Return a natural-language interpretation of a p-value."""
    if p < 0.001:
        return f"p < .001, which is statistically significant at α = {alpha}"
    elif p < alpha:
        return f"p = {p:.3f}, which is statistically significant at α = {alpha}"
    elif p < 0.10:
        return f"p = {p:.3f}, which is marginally significant (trend-level)"
    else:
        return f"p = {p:.3f}, which is not statistically significant at α = {alpha}"


def interpret_correlation_strength(r: float) -> str:
    """Cohen's conventions for correlation strength."""
    r_abs = abs(r)
    if r_abs < 0.1:
        return "negligible"
    elif r_abs < 0.3:
        return "weak"
    elif r_abs < 0.5:
        return "moderate"
    else:
        return "strong"


def interpret_correlation_direction(r: float) -> str:
    if r > 0:
        return "positive"
    elif r < 0:
        return "negative"
    return "no"


def interpret_cohens_d(d: float) -> str:
    """Cohen's conventions for d."""
    d_abs = abs(d)
    if d_abs < 0.2:
        return "negligible"
    elif d_abs < 0.5:
        return "small"
    elif d_abs < 0.8:
        return "medium"
    else:
        return "large"


# ── Aliases for stat engine method names ────────────────────────────

register_alias("descriptives", "descriptive_statistics")
register_alias("frequencies", "frequency_analysis")


def format_value(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}"
