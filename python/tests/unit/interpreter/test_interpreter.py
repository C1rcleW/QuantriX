"""Tests for the ResultInterpreter."""

import pytest

from quantrix.interpreter.engine import InterpretationResult, ResultInterpreter


class TestResultInterpreter:
    @pytest.fixture
    def interpreter(self):
        return ResultInterpreter()

    def test_ttest_interpretation(self, interpreter):
        result = interpreter.interpret(
            "independent_ttest",
            {
                "dv_label": "Income",
                "iv_label": "Gender",
                "group_labels": ["Male", "Female"],
                "means": [49200, 41000],
                "sds": [12000, 10500],
                "ns": [600, 647],
                "sig_text": "p < .001, which is statistically significant",
                "effect_size_text": "Cohen's d = 0.38, a small effect size.",
            },
        )
        assert "Income" in result.summary
        assert "p < .001" in result.detailed
        assert "Male" in result.detailed
        assert "Cohen's d" in result.detailed

    def test_correlation_interpretation(self, interpreter):
        result = interpreter.interpret(
            "pearson_correlation",
            {
                "dv_label": "Income",
                "iv_label": "Education (years)",
                "r": 0.45,
                "df": 1245,
                "p_value": 0.001,
                "n": 1247,
            },
        )
        assert "correlation" in result.summary.lower()
        assert len(result.key_findings) >= 1

    def test_anova_interpretation(self, interpreter):
        result = interpreter.interpret(
            "oneway_anova",
            {
                "dv_label": "Test Score",
                "iv_label": "Education Level",
                "n_groups": 4,
                "p_value": 0.003,
                "eta_squared": 0.12,
                "sig_text": "p = .003, statistically significant",
                "effect_size_text": "η² = 0.12 (medium effect)",
                "group_table": "",
                "posthoc_note": "",
            },
        )
        assert "Test Score" in result.summary
        assert "p = .003" in result.detailed

    def test_descriptive_interpretation(self, interpreter):
        result = interpreter.interpret(
            "descriptive_statistics",
            {
                "dv_label": "Age",
                "n": 100,
                "n_valid": 95,
                "missing_count": 5,
                "missing_pct": 5.0,
                "mean": 35.2,
                "std_dev": 10.5,
                "min_val": 18.0,
                "max_val": 65.0,
                "skewness_text": "",
            },
        )
        assert "35.2" in result.detailed
        assert len(result.summary) > 0

    def test_unknown_method_returns_gracefully(self, interpreter):
        result = interpreter.interpret("unknown_method", {"dv_label": "X"})
        assert result.summary != ""
        assert isinstance(result, InterpretationResult)

    def test_safety_warnings_become_limitations(self, interpreter):
        result = interpreter.interpret(
            "independent_ttest",
            {
                "dv_label": "Income",
                "iv_label": "Gender",
                "group_labels": ["A", "B"],
                "means": [1, 2],
                "sds": [1, 1],
                "ns": [10, 10],
                "sig_text": "p = .045",
                "effect_size_text": "",
            },
            safety_warnings=[
                {"severity": "warning", "message": "Sample size is small (N=20)."},
                {"severity": "info", "message": "Data is clean."},
            ],
        )
        assert len(result.limitations) == 1
        assert "sample size" in result.limitations[0].lower()

    def test_key_findings_significance(self, interpreter):
        result = interpreter.interpret(
            "chi_square",
            {
                "dv_label": "Gender",
                "iv_label": "Region",
                "p_value": 0.002,
                "chi_sq": 15.3,
                "df": 3,
                "n": 500,
            },
        )
        assert any("significant" in f.lower() for f in result.key_findings)
