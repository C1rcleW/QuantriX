"""Variable type inference engine.

Refines raw reader-level type assignments using distribution and
cardinality analysis. The reader gives a conservative estimate;
the TypeDetector improves it.

Rules (ordered by priority):
1. Float columns are always CONTINUOUS (they have decimal precision)
2. Boolean columns are always NOMINAL
3. String columns: low cardinality → likely NOMINAL
4. Integer columns: low cardinality → likely categorical (ORDINAL if ordered)
5. High-cardinality strings remain STRING
"""

from __future__ import annotations

import polars as pl

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType

# Thresholds
LOW_CARDINALITY_THRESHOLD = 15  # Fewer unique values → likely categorical
HIGH_CARDINALITY_RATIO = 0.8  # unique/n > 0.8 → likely continuous/string


class TypeDetector:
    """Refine variable type assignments based on data analysis.

    Usage:
        detector = TypeDetector()
        refined = detector.refine(dataset)
        # dataset.variables now have improved type assignments
    """

    def refine(self, variables: list[VariableMetadata], df: pl.DataFrame) -> None:
        """Refine variable types in-place.

        Args:
            variables: List of VariableMetadata to refine (mutated in-place).
            df: The Polars DataFrame with the actual data.
        """
        for var in variables:
            if var.name not in df.columns:
                continue

            col = df[var.name]
            valid = col.drop_nulls()
            n_total = len(col)
            n_valid = len(valid)
            n_unique = var.n_unique or (valid.n_unique() if n_valid > 0 else 0)

            new_type = self._infer_type(
                current_type=var.variable_type,
                n_total=n_total,
                n_valid=n_valid,
                n_unique=n_unique,
                dtype=col.dtype,
                has_nulls=n_total > n_valid,
            )

            if new_type != var.variable_type:
                var.variable_type = new_type

    @staticmethod
    def _infer_type(
        current_type: VariableType,
        n_total: int,
        n_valid: int,
        n_unique: int,
        dtype: pl.DataType,
        has_nulls: bool,  # noqa: ARG004 (reserved for future rules)
    ) -> VariableType:
        """Infer the best VariableType given column statistics.

        The rules are applied in priority order. First match wins.
        """
        # Rule 1: Floats are always continuous
        if dtype in (pl.Float64, pl.Float32):
            return VariableType.CONTINUOUS

        # Rule 2: Booleans are always nominal
        if dtype == pl.Boolean:
            return VariableType.NOMINAL

        # Rule 3: String columns
        if dtype == pl.String:
            if n_unique <= LOW_CARDINALITY_THRESHOLD:
                return VariableType.NOMINAL
            return VariableType.STRING

        # Rule 4: Integer columns — cardinality analysis
        if dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8,
                      pl.UInt64, pl.UInt32, pl.UInt16, pl.UInt8):
            # No valid data → keep current type
            if n_valid == 0:
                return current_type

            # Very low cardinality → categorical
            if n_unique <= 2:
                return VariableType.NOMINAL
            if n_unique <= LOW_CARDINALITY_THRESHOLD:
                # Only reclassify if few values are unique relative to total
                if n_valid > 0 and n_unique / n_valid < 0.5:
                    return VariableType.ORDINAL
                # High ratio of unique values suggests continuous data
                return VariableType.CONTINUOUS

            # High cardinality ratio → continuous (e.g., ID column)
            if n_unique / n_valid > HIGH_CARDINALITY_RATIO:
                return VariableType.CONTINUOUS

            return VariableType.CONTINUOUS

        # Rule 5: Categorical/Enum → nominal
        if dtype in (pl.Categorical, pl.Enum):
            return VariableType.NOMINAL

        # Fallback
        return current_type


def refine_variable_types(
    variables: list[VariableMetadata],
    df: pl.DataFrame,
) -> list[VariableMetadata]:
    """Convenience function: refine types and return the updated list."""
    detector = TypeDetector()
    detector.refine(variables, df)
    return variables


def suggest_ordinal_from_labels(
    variables: list[VariableMetadata],
) -> list[VariableMetadata]:
    """Heuristic: if a nominal variable has value labels that look ordered
    (numeric keys in ascending order), reclassify as ordinal.

    This catches cases like Likert scales stored as labeled integers.
    """
    for var in variables:
        if var.variable_type != VariableType.NOMINAL:
            continue
        if not var.value_labels:
            continue

        # Check if all label keys are numeric and form a plausible ordinal sequence
        keys = [vl.value for vl in var.value_labels if isinstance(vl.value, (int, float))]
        if len(keys) >= 3 and keys == sorted(keys):
            # Looks like an ordinal scale (e.g., 1=Disagree, 2=Neutral, 3=Agree)
            var.variable_type = VariableType.ORDINAL

    return variables
