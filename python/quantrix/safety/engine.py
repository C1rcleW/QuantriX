"""Statistical Safety Net — engine and warning types.

The SafetyNet runs all registered safety rules against a proposed analysis
and collects warnings. Rules are deterministic — no LLM involvement.

Architecture:
    SafetyNet
      ├── TypeMatchRule       (variable type × method compatibility)
      ├── SampleSizeRule      (minimum N per group/cell)
      ├── NormalityRule       (Shapiro-Wilk, skewness heuristic)
      ├── HomogeneityRule     (variance equality for group comparisons)
      ├── OutlierRule         (IQR-based detection)
      └── MultipleComparisonRule (Bonferroni reminder)

Each rule returns a list of SafetyWarning. The engine collects them all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata


@dataclass
class SafetyWarning:
    """A single warning or error raised by a safety rule."""

    rule_name: str
    severity: str  # "error" (blocks), "warning" (advisory), "info"
    message: str
    suggestion: str = ""
    variable_names: list[str] = field(default_factory=list)


@dataclass
class SafetyReport:
    """Aggregated safety check results."""

    method_name: str
    passed: list[SafetyWarning] = field(default_factory=list)  # severity = info
    warnings: list[SafetyWarning] = field(default_factory=list)  # severity = warning
    errors: list[SafetyWarning] = field(default_factory=list)  # severity = error

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def is_clean(self) -> bool:
        return not self.has_errors and not self.has_warnings

    def to_dict(self) -> dict:
        return {
            "method_name": self.method_name,
            "is_clean": self.is_clean,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "errors": [
                {
                    "rule": w.rule_name,
                    "severity": w.severity,
                    "message": w.message,
                    "suggestion": w.suggestion,
                    "variables": w.variable_names,
                }
                for w in self.errors
            ],
            "warnings": [
                {
                    "rule": w.rule_name,
                    "severity": w.severity,
                    "message": w.message,
                    "suggestion": w.suggestion,
                    "variables": w.variable_names,
                }
                for w in self.warnings
            ],
            "info": [
                {"rule": w.rule_name, "severity": w.severity, "message": w.message}
                for w in self.passed
            ],
        }


class SafetyRule:
    """Base class for safety rules.

    Each rule implements check() and returns a list of SafetyWarning.
    Empty list means the check passed.
    """

    rule_name: str = "base"
    rule_description: str = ""

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> list[SafetyWarning]:
        raise NotImplementedError


class SafetyNet:
    """Runs all safety rules and produces a SafetyReport."""

    def __init__(self) -> None:
        self.rules: list[SafetyRule] = []

    def register(self, rule: SafetyRule) -> None:
        self.rules.append(rule)

    def check(
        self,
        method_name: str,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
        dataset: Dataset,
    ) -> SafetyReport:
        report = SafetyReport(method_name=method_name)

        for rule in self.rules:
            try:
                results = rule.check(method_name, dv, ivs, dataset)
                for w in results:
                    if w.severity == "error":
                        report.errors.append(w)
                    elif w.severity == "warning":
                        report.warnings.append(w)
                    else:
                        report.passed.append(w)
            except Exception as e:
                report.errors.append(
                    SafetyWarning(
                        rule_name=rule.rule_name,
                        severity="error",
                        message=f"Rule execution failed: {e}",
                    )
                )

        return report


def create_default_safety_net() -> SafetyNet:
    """Factory: build a SafetyNet with all standard rules registered."""
    from quantrix.safety.rules.homogeneity import HomogeneityRule
    from quantrix.safety.rules.multiple_comparison import MultipleComparisonRule
    from quantrix.safety.rules.normality import NormalityRule
    from quantrix.safety.rules.outliers import OutlierRule
    from quantrix.safety.rules.sample_size import SampleSizeRule
    from quantrix.safety.rules.type_match import TypeMatchRule

    net = SafetyNet()
    net.register(TypeMatchRule())
    net.register(SampleSizeRule())
    net.register(NormalityRule())
    net.register(HomogeneityRule())
    net.register(OutlierRule())
    net.register(MultipleComparisonRule())
    return net
