"""Missing data pattern detector.

Analyses missing value patterns across variables and cases.
Provides heuristic MCAR/MAR classification and per-variable
missing summaries.

Note: True MCAR testing requires Little's MCAR test (chi-squared),
which is deferred to the stats engine. This module provides
descriptive heuristics instead.
"""

from __future__ import annotations

import polars as pl

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import MissingPattern


class MissingDetector:
    """Detect and classify missing data patterns.

    Usage:
        detector = MissingDetector()
        detector.analyze(variables, df)
    """

    def analyze(self, variables: list[VariableMetadata], df: pl.DataFrame) -> None:
        """Analyze missing patterns and update variable metadata in-place.

        Populates:
        - missing_count, missing_percentage per variable
        - missing_pattern (MCAR/MAR/MNAR heuristic)
        - n_valid per variable
        """
        # Per-variable missing stats (already partially filled by enrich_metadata_from_data)
        for var in variables:
            if var.name in df.columns:
                col = df[var.name]
                var.missing_count = col.null_count()
                var.missing_percentage = (
                    var.missing_count / len(col) * 100 if len(col) > 0 else 0.0
                )
                var.n_valid = len(col) - var.missing_count

        # Classify overall missing pattern
        self._classify_pattern(variables, df)

    @staticmethod
    def _classify_pattern(
        variables: list[VariableMetadata], df: pl.DataFrame
    ) -> None:
        """Heuristic missing pattern classification.

        MCAR: < 5% missing overall, and missing values appear random
        MAR:  Missingness correlates with observed variables
        MNAR: > 20% missing on any variable, or systematic patterns

        This is intentionally conservative. The classification is
        advisory, not definitive.
        """
        n_total = len(df)
        if n_total == 0:
            return

        # Calculate overall missing rate
        total_missing = sum(v.missing_count for v in variables)
        total_cells = n_total * max(len(variables), 1)
        overall_rate = total_missing / total_cells * 100 if total_cells > 0 else 0.0

        # Per-variable missing rate
        max_rate = max((v.missing_percentage for v in variables), default=0.0)

        # Simple heuristic classification
        for var in variables:
            if var.missing_count == 0:
                var.missing_pattern = MissingPattern.UNKNOWN
                continue

            if max_rate > 20.0:
                # High missing rate suggests systematic missingness
                var.missing_pattern = MissingPattern.MNAR
            elif overall_rate < 5.0:
                var.missing_pattern = MissingPattern.MCAR
            else:
                var.missing_pattern = MissingPattern.MAR

    @staticmethod
    def missing_summary_table(
        variables: list[VariableMetadata],
    ) -> list[dict[str, object]]:
        """Generate a summary table of missing values per variable."""
        return [
            {
                "variable": v.name,
                "missing_count": v.missing_count,
                "missing_pct": round(v.missing_percentage, 1),
                "n_valid": v.n_valid,
                "pattern": v.missing_pattern.value,
            }
            for v in variables
        ]

    @staticmethod
    def case_missing_counts(df: pl.DataFrame) -> pl.DataFrame:
        """Count missing values per case (row).

        Returns a DataFrame with a 'missing_count' column.
        """
        missing_per_row = []
        for row in df.iter_rows(named=False):
            nulls = sum(1 for val in row if val is None)
            missing_per_row.append(nulls)

        return pl.DataFrame({"missing_count": missing_per_row})
