"""Data profile generator.

Produces a structured, human-readable (and LLM-consumable) overview
of a Dataset. This is the "AI understands the data" step in the
Quantrix workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata


@dataclass
class DataProfile:
    """A complete data profile for a Dataset.

    Designed for two consumers:
    1. The GUI: renders as variable cards with quality indicators
    2. The AI Agent: serialized as prompt context for analysis recommendations
    """

    dataset_name: str
    source_format: str
    n_rows: int
    n_columns: int

    # Overall statistics
    total_missing_cells: int
    overall_missing_rate: float  # percentage
    n_complete_cases: int
    n_incomplete_cases: int

    # Variable profiles
    variable_profiles: list[VariableProfile] = field(default_factory=list)

    # Quality flags
    has_high_missing: bool = False  # Any variable > 20% missing
    has_outliers: bool = False
    has_constant_variables: bool = False  # Zero-variance columns

    def to_markdown(self) -> str:
        """Render as Markdown (for LLM prompt context)."""
        lines = [
            f"# Data Profile: {self.dataset_name}",
            "",
            f"- **Rows**: {self.n_rows}",
            f"- **Columns**: {self.n_columns}",
            f"- **Source format**: {self.source_format}",
            f"- **Missing cells**: {self.total_missing_cells} ({self.overall_missing_rate:.1f}%)",
            f"- **Complete cases**: {self.n_complete_cases}/{self.n_rows}",
            "",
        ]

        if self.has_high_missing:
            lines.append("⚠️ **Warning**: Some variables have high missing rates (>20%).")
            lines.append("")

        if self.has_constant_variables:
            lines.append("⚠️ **Warning**: Some variables have zero variance.")
            lines.append("")

        lines.append("## Variable Overview")
        lines.append("")

        for vp in self.variable_profiles:
            lines.append(f"### {vp.display_name} (`{vp.name}`)")
            lines.append(f"- **Type**: {vp.variable_type}")
            lines.append(f"- **Valid**: {vp.n_valid}/{vp.n_total} ({vp.completeness_pct:.1f}% complete)")
            if vp.n_unique is not None:
                lines.append(f"- **Unique values**: {vp.n_unique}")

            if vp.variable_type == "continuous":
                if vp.min_value is not None:
                    lines.append(f"- **Range**: {vp.min_value:.2f} – {vp.max_value:.2f}")
                if vp.mean is not None:
                    lines.append(f"- **Mean**: {vp.mean:.2f}, **SD**: {vp.std_dev:.2f}")

            if vp.value_labels_summary:
                lines.append(f"- **Value labels**: {vp.value_labels_summary}")

            if vp.quality_note:
                lines.append(f"- ⚠️ {vp.quality_note}")

            lines.append("")

        return "\n".join(lines)


@dataclass
class VariableProfile:
    """A single variable's profile for display and AI context."""

    name: str
    display_name: str
    variable_type: str
    n_total: int
    n_valid: int
    n_unique: int | None

    # Completeness
    completeness_pct: float

    # Continuous stats (None for categorical)
    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None
    std_dev: float | None = None

    # Categorical stats
    value_labels_summary: str = ""

    # Quality
    quality_note: str = ""


class ProfileGenerator:
    """Generate a DataProfile from a Dataset."""

    def generate(self, dataset: Dataset) -> DataProfile:
        """Produce a complete data profile."""
        df = dataset.data
        if df is None:
            return DataProfile(
                dataset_name=dataset.name,
                source_format=dataset.source_format,
                n_rows=0,
                n_columns=0,
                total_missing_cells=0,
                overall_missing_rate=0.0,
                n_complete_cases=0,
                n_incomplete_cases=0,
            )

        # Variable profiles
        var_profiles = [
            self._build_variable_profile(var, df[var.name])
            for var in dataset.variables
        ]

        # Missing stats
        total_missing = sum(vp.n_total - vp.n_valid for vp in var_profiles)
        total_cells = dataset.n_rows * max(dataset.n_columns, 1)
        overall_rate = total_missing / total_cells * 100 if total_cells > 0 else 0.0

        # Case completeness
        missing_per_row = self._count_missing_per_row(df)
        n_complete = sum(1 for m in missing_per_row if m == 0)
        n_incomplete = dataset.n_rows - n_complete

        # Quality flags
        has_high_missing = any(
            vp.completeness_pct < 80.0 for vp in var_profiles
        )
        has_constant = any(
            vp.n_unique is not None and vp.n_unique <= 1 for vp in var_profiles
        )

        return DataProfile(
            dataset_name=dataset.name,
            source_format=dataset.source_format,
            n_rows=dataset.n_rows,
            n_columns=dataset.n_columns,
            total_missing_cells=total_missing,
            overall_missing_rate=round(overall_rate, 2),
            n_complete_cases=n_complete,
            n_incomplete_cases=n_incomplete,
            variable_profiles=var_profiles,
            has_high_missing=has_high_missing,
            has_constant_variables=has_constant,
        )

    @staticmethod
    def _build_variable_profile(
        var: VariableMetadata, col: pl.Series,
    ) -> VariableProfile:
        """Build a VariableProfile from metadata and data."""

        # Compute missing stats from actual column data (authoritative)
        n_total = len(col)
        n_valid = n_total - col.null_count()
        actual_missing_pct = col.null_count() / n_total * 100 if n_total > 0 else 0.0

        quality_notes: list[str] = []

        if actual_missing_pct > 20:
            quality_notes.append(f"High missing rate ({actual_missing_pct:.1f}%)")
        elif actual_missing_pct > 5:
            quality_notes.append(f"Moderate missing rate ({actual_missing_pct:.1f}%)")

        if var.skewness is not None and abs(var.skewness) > 2:
            quality_notes.append(f"Highly skewed (skewness={var.skewness:.1f})")

        if var.outlier_count > 0:
            quality_notes.append(f"{var.outlier_count} potential outliers")

        # Value labels summary
        labels_summary = ""
        if var.value_labels:
            preview = ", ".join(
                f"{vl.value}={vl.label}" for vl in var.value_labels[:5]
            )
            if len(var.value_labels) > 5:
                preview += f" (+{len(var.value_labels) - 5} more)"
            labels_summary = preview

        return VariableProfile(
            name=var.name,
            display_name=var.display_name,
            variable_type=var.variable_type.value,
            n_total=n_total,
            n_valid=n_valid,
            n_unique=var.n_unique,
            completeness_pct=round(100 - actual_missing_pct, 1),
            min_value=var.min_value,
            max_value=var.max_value,
            mean=var.mean,
            std_dev=var.std_dev,
            value_labels_summary=labels_summary,
            quality_note="; ".join(quality_notes) if quality_notes else "",
        )

    @staticmethod
    def _count_missing_per_row(df: pl.DataFrame) -> list[int]:
        """Count nulls per row."""

        missing_per_row: list[int] = []
        for row in df.iter_rows(named=False):
            nulls = sum(1 for val in row if val is None)
            missing_per_row.append(nulls)
        return missing_per_row
