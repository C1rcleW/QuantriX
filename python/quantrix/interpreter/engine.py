"""Result interpreter engine.

Fills interpretation templates with analysis results to produce
natural-language explanations that researchers can use directly
in their papers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InterpretationResult:
    """Structured interpretation output."""

    method_name: str
    summary: str               # One-sentence summary
    detailed: str              # Full markdown interpretation
    key_findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class ResultInterpreter:
    """Interprets statistical output as natural language.

    Phase 4 is template-only. Phase 6 will add LLM polish.

    Usage:
        interpreter = ResultInterpreter()
        result = interpreter.interpret("independent_ttest", {
            "dv_label": "Income",
            "iv_label": "Gender",
            "t_stat": 3.42,
            "p_value": 0.0006,
            ...
        })
        print(result.detailed)
    """

    def interpret(
        self, method_name: str, stats: dict, safety_warnings: list[dict] | None = None
    ) -> InterpretationResult:
        """Generate an interpretation from analysis statistics.

        Args:
            method_name: e.g., "independent_ttest", "pearson_correlation"
            stats: Key-value pairs from the analysis (varies by method).
            safety_warnings: Optional list of safety check results.

        Returns:
            InterpretationResult with summary, detailed text, and key findings.
        """
        from quantrix.interpreter.template_registry import get as get_template

        template = get_template(method_name)
        detailed = ""
        key_findings: list[str] = []
        limitations: list[str] = []

        if template:
            try:
                # Fill defaults for optional template fields
                defaults = dict.fromkeys(
                    ["cell_note", "group_table", "posthoc_note", "skewness_text",
                     "note", "missing_pct", "coefficient_table", "effect_size_text",
                     "sig_text", "group_labels", "n_groups", "n", "n_valid"], "")
                defaults["means"] = []
                defaults["sds"] = []
                defaults["ns"] = []
                defaults.update(stats)
                detailed = template.format(**defaults)
            except KeyError as e:
                detailed = f"(Template error: missing key {e})"

        # Build summary
        summary = self._build_summary(method_name, stats)

        # Extract key findings
        key_findings = self._extract_key_findings(method_name, stats)

        # Add limitations from safety warnings
        if safety_warnings:
            for w in safety_warnings:
                if w.get("severity") == "warning":
                    limitations.append(w.get("message", ""))

        return InterpretationResult(
            method_name=method_name,
            summary=summary,
            detailed=detailed,
            key_findings=key_findings,
            limitations=limitations,
        )

    def _build_summary(self, method_name: str, stats: dict) -> str:
        """Build a one-sentence summary."""
        from quantrix.interpreter.template_registry import (
            format_value,
            interpret_cohens_d,
            interpret_correlation_strength,
            interpret_p_value,
        )

        p = stats.get("p_value")
        dv = stats.get("dv_label", "the outcome")
        iv = stats.get("iv_label", "the predictor")

        if method_name == "independent_ttest":
            sig_text = ""
            if p is not None:
                sig_text = interpret_p_value(float(p))
            d = stats.get("cohens_d")
            es_text = ""
            if d is not None:
                es_text = f", {interpret_cohens_d(float(d))} effect size (d = {float(d):.2f})"
            return f"The difference in {dv} between groups of {iv} was {sig_text}{es_text}."

        elif method_name in ("oneway_anova", "kruskal_wallis"):
            sig_text = interpret_p_value(float(p)) if p is not None else ""
            eta = stats.get("eta_squared")
            es_text = f", η² = {float(eta):.3f}" if eta is not None else ""
            return f"The comparison of {dv} across groups of {iv} was {sig_text}{es_text}."

        elif method_name == "pearson_correlation":
            r_val = stats.get("r")
            if r_val is not None:
                r = float(r_val)
                strength = interpret_correlation_strength(r)
                direction = "positive" if r >= 0 else "negative"
                sig_text = interpret_p_value(float(p)) if p is not None else ""
                return (
                    f"A {strength} {direction} correlation was found "
                    f"between {dv} and {iv}, r = {r:.3f}, {sig_text}."
                )
            return f"Correlation between {dv} and {iv} was computed."

        elif method_name == "linear_regression":
            r2 = stats.get("r_squared")
            sig_text = interpret_p_value(float(p)) if p is not None else ""
            if r2 is not None:
                return (
                    f"The model predicting {dv} was {sig_text}, "
                    f"explaining {float(r2)*100:.1f}% of the variance."
                )
            return f"Regression model for {dv} was {sig_text}."

        elif method_name == "chi_square":
            sig_text = interpret_p_value(float(p)) if p is not None else ""
            return (
                f"The association between {dv} and {iv} was {sig_text}."
            )

        elif method_name in ("descriptive_statistics", "descriptives"):
            mean = stats.get("mean")
            n = stats.get("n_valid", "N/A")
            if mean is not None:
                return f"The average {dv} was {float(mean):.2f} (N = {n})."
            return f"Descriptive statistics for {dv} (N = {n})."

        elif method_name in ("frequency_analysis", "frequencies"):
            mode = stats.get("mode_category", "")
            n = stats.get("n", "N/A")
            if mode:
                return f"The most common category for {dv} was '{mode}' (N = {n})."
            return f"Frequency analysis for {dv} (N = {n})."

        return f"Analysis of {dv} completed."

    @staticmethod
    def _extract_key_findings(method_name: str, stats: dict) -> list[str]:
        """Extract key findings as bullet points."""
        findings: list[str] = []

        p = stats.get("p_value")
        if p is not None and float(p) < 0.05:
            findings.append(f"Statistically significant result (p = {float(p):.4f})")

        d = stats.get("cohens_d")
        if d is not None:
            from quantrix.interpreter.template_registry import interpret_cohens_d
            findings.append(
                f"Effect size: {interpret_cohens_d(float(d))} "
                f"(Cohen's d = {float(d):.2f})"
            )

        r2 = stats.get("r_squared")
        if r2 is not None:
            findings.append(f"Model explains {float(r2)*100:.1f}% of variance")

        return findings
