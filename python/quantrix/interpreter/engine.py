"""Result interpreter engine.

Fills interpretation templates with analysis results to produce
natural-language explanations that researchers can use directly
in their papers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InterpretationResult:
    """Structured interpretation output."""

    method_name: str
    summary: str  # One-sentence summary
    detailed: str  # Full markdown interpretation
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
        self,
        method_name: str,
        stats: dict[str, Any],
        safety_warnings: list[dict[str, Any]] | None = None,
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
        key_findings: list[str] = []
        limitations: list[str] = []
        summary = self._build_summary(method_name, stats)
        detailed = summary

        if template:
            try:
                # Fill defaults for optional template fields
                defaults: dict[str, Any] = dict.fromkeys(
                    [
                        "cell_note",
                        "group_table",
                        "posthoc_note",
                        "skewness_text",
                        "note",
                        "missing_pct",
                        "coefficient_table",
                        "effect_size_text",
                        "sig_text",
                        "group_labels",
                        "n_groups",
                        "n",
                        "n_valid",
                        "mode_pct",
                        "strength",
                        "direction",
                    ],
                    "",
                )
                defaults["means"] = []
                defaults["sds"] = []
                defaults["ns"] = []
                defaults["missing_pct"] = 0.0
                defaults["mode_pct"] = 0.0
                defaults.update(stats)
                detailed = template.format(**defaults)
            except (KeyError, ValueError, TypeError, IndexError):
                detailed = summary

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

    @staticmethod
    def _finite(value: Any) -> float | None:
        """Return a finite float, or None for missing/invalid/non-finite values."""
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if math.isfinite(result) else None

    def _build_summary(self, method_name: str, stats: dict[str, Any]) -> str:
        """Build a one-sentence summary."""
        from quantrix.interpreter.template_registry import (
            interpret_cohens_d,
            interpret_correlation_strength,
            interpret_p_value,
        )

        p = self._finite(stats.get("p_value"))
        dv = str(stats.get("dv_label") or "the outcome")
        iv = str(stats.get("iv_label") or "the predictor")
        if p is not None:
            p_text = interpret_p_value(p)
        else:
            p_text = "not evaluated (insufficient or invalid statistics)"

        if method_name == "independent_ttest":
            sig_text = p_text
            d = self._finite(stats.get("cohens_d"))
            es_text = ""
            if d is not None:
                es_text = f", {interpret_cohens_d(d)} effect size (d = {d:.2f})"
            return f"The difference in {dv} between groups of {iv} was {sig_text}{es_text}."

        elif method_name in ("oneway_anova", "kruskal_wallis"):
            sig_text = p_text
            eta = self._finite(stats.get("eta_squared"))
            es_text = f", η² = {eta:.3f}" if eta is not None else ""
            return f"The comparison of {dv} across groups of {iv} was {sig_text}{es_text}."

        elif method_name == "pearson_correlation":
            r = self._finite(stats.get("r"))
            if r is not None:
                strength = interpret_correlation_strength(r)
                direction = "positive" if r >= 0 else "negative"
                return (
                    f"A {strength} {direction} correlation was found "
                    f"between {dv} and {iv}, r = {r:.3f}, {p_text}."
                )
            return f"Correlation between {dv} and {iv} was computed."

        elif method_name == "spearman_correlation":
            rho = self._finite(stats.get("rho"))
            if rho is not None:
                strength = interpret_correlation_strength(rho)
                direction = "positive" if rho >= 0 else "negative"
                return (
                    f"A {strength} {direction} monotonic correlation was found "
                    f"between {dv} and {iv}, rho = {rho:.3f}, {p_text}."
                )
            return f"Spearman correlation between {dv} and {iv} was computed."

        elif method_name == "linear_regression":
            r2 = self._finite(stats.get("r_squared"))
            if r2 is not None:
                return (
                    f"The model predicting {dv} was {p_text}, "
                    f"explaining {r2 * 100:.1f}% of the variance."
                )
            return f"Regression model for {dv} was {p_text}."

        elif method_name == "chi_square":
            return f"The association between {dv} and {iv} was {p_text}."

        elif method_name in ("descriptive_statistics", "descriptives"):
            mean = self._finite(stats.get("mean"))
            n = stats.get("n_valid", "N/A")
            if mean is not None:
                return f"The average {dv} was {mean:.2f} (N = {n})."
            return f"Descriptive statistics for {dv} (N = {n})."

        elif method_name in ("frequency_analysis", "frequencies"):
            mode = stats.get("mode_category", "")
            n = stats.get("n", "N/A")
            if mode:
                return f"The most common category for {dv} was '{mode}' (N = {n})."
            return f"Frequency analysis for {dv} (N = {n})."

        return f"Analysis of {dv} completed."

    @staticmethod
    def _extract_key_findings(method_name: str, stats: dict[str, Any]) -> list[str]:
        """Extract key findings as bullet points."""
        findings: list[str] = []

        p = ResultInterpreter._finite(stats.get("p_value"))
        if p is not None and p < 0.05:
            findings.append(f"Statistically significant result (p = {p:.4f})")

        d = ResultInterpreter._finite(stats.get("cohens_d"))
        if d is not None:
            from quantrix.interpreter.template_registry import interpret_cohens_d

            findings.append(f"Effect size: {interpret_cohens_d(d)} (Cohen's d = {d:.2f})")

        r2 = ResultInterpreter._finite(stats.get("r_squared"))
        if r2 is not None:
            findings.append(f"Model explains {r2 * 100:.1f}% of variance")

        return findings
