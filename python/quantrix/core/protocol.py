"""Plugin protocol definitions.

Every extension point in Quantrix is defined as a Protocol, not an ABC.
This allows third-party packages to implement plugins without depending
on Quantrix internals—they just need to match the structural contract.

Protocols are checked at registration time (runtime structural subtyping),
not at import time.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata

# ── Data I/O ──────────────────────────────────────────────────────────────


@runtime_checkable
class ReaderProtocol(Protocol):
    """Read a data file and produce a Dataset.

    Each reader handles one format (SAV, CSV, XLSX, DTA).
    Readers are auto-discovered via entry points.
    """

    format_name: str
    format_extensions: list[str]

    def read(self, path: str) -> Dataset:
        """Read a file and return a Dataset with metadata."""
        ...


@runtime_checkable
class WriterProtocol(Protocol):
    """Write a Dataset to a file format."""

    format_name: str
    format_extensions: list[str]

    def write(self, dataset: Dataset, path: str) -> None:
        """Write dataset to the given path."""
        ...


# ── Statistical Methods ──────────────────────────────────────────────────


@runtime_checkable
class StatMethodProtocol(Protocol):
    """A statistical analysis method.

    Each method (t-test, ANOVA, regression, etc.) implements this protocol.
    The orchestration layer calls these without knowing the internals.
    """

    method_name: str
    method_family: str  # "descriptive", "comparison", "correlation", "regression", "dimensionality"
    required_variable_types: dict[str, list[str]]
    # e.g., {"dependent": ["continuous"], "independent": ["nominal", "ordinal"]}

    def can_handle(self, variables: list[VariableMetadata], research_question_type: str) -> bool:
        """Whether this method is appropriate for the given variables and question."""
        ...

    def execute(self, dataset: Dataset, **params: object) -> AnalysisResult:
        """Run the analysis and return structured results."""
        ...


# ── Safety Rules ──────────────────────────────────────────────────────────


@runtime_checkable
class SafetyRuleProtocol(Protocol):
    """A single statistical assumption check.

    Each rule checks one assumption (normality, homogeneity, sample size, etc.)
    for a given method and set of variables. Rules are collected into the
    SafetyEngine and run as a pipeline.
    """

    rule_name: str
    rule_description: str
    severity: str  # "error" (blocks analysis), "warning" (advisory), "info"

    def check(
        self, method_name: str, variables: list[VariableMetadata], dataset: Dataset
    ) -> list[SafetyWarning]:
        """Check the assumption. Returns empty list if passed."""
        ...


# ── Result Types ──────────────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    """Structured output from any statistical method.

    This is the contract between the stats engine and the UI/report engine.
    Every StatMethodProtocol.execute() returns this.
    """

    method_name: str
    method_family: str
    n_samples: int

    # Key-value results (e.g., {"t": 3.42, "df": 1245, "p": 0.0006})
    statistics: dict[str, float] = Field(default_factory=dict)

    # Effect sizes
    effect_sizes: dict[str, float] = Field(default_factory=dict)

    # Tables (for display)
    tables: list[ResultTable] = Field(default_factory=list)

    # Figures (base64-encoded or paths)
    figures: list[ResultFigure] = Field(default_factory=list)

    # Natural language interpretation (populated by interpreter)
    interpretation: str = ""

    # Warnings raised during execution
    warnings: list[SafetyWarning] = Field(default_factory=list)

    # Raw provenance for DAG
    execution_time_ms: float = 0.0


class ResultTable(BaseModel):
    """A single output table (e.g., group descriptives, ANOVA summary)."""

    title: str
    columns: list[str]
    rows: list[list[str | float | None]]
    notes: str = ""


class ResultFigure(BaseModel):
    """A single output figure."""

    title: str
    format: str = "svg"  # "svg", "png"
    data: str = ""  # Base64-encoded image data
    alt_text: str = ""


class SafetyWarning(BaseModel):
    """A warning or error raised by the safety net."""

    rule_name: str
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: str = ""  # What the researcher should do
    variable_names: list[str] = Field(default_factory=list)
