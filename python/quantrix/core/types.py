"""Fundamental enumerations shared across the platform.

These types mirror SPSS measurement levels and variable types but are
extended to support Polars-native dtype mapping and AI-driven inference.
"""

from enum import StrEnum


class VariableType(StrEnum):
    """Statistical variable type, combining storage type and measurement intent.

    This is the unified type used throughout Quantrix. It deliberately
    conflates storage and measurement to reduce the cognitive load on
    researchers—they see one type, not two orthogonal dimensions.

    Mapping to SPSS:
        Scale     → continuous
        Ordinal   → ordinal
        Nominal   → nominal
        String    → string (SPSS "String" variables, treated as nominal)
    """

    CONTINUOUS = "continuous"  # Interval/ratio scale (SPSS: Scale)
    ORDINAL = "ordinal"  # Ordered categories (SPSS: Ordinal)
    NOMINAL = "nominal"  # Unordered categories (SPSS: Nominal)
    STRING = "string"  # Free-text (SPSS: String)


class MeasureLevel(StrEnum):
    """Stevens' measurement levels, preserved for statistical correctness.

    Stored as a separate field from VariableType because some operations
    (e.g., PCA, reliability analysis) need to distinguish interval from ratio.
    """

    NOMINAL = "nominal"
    ORDINAL = "ordinal"
    INTERVAL = "interval"
    RATIO = "ratio"


class MissingPattern(StrEnum):
    """High-level missing data pattern classification.

    MCAR = Missing Completely At Random (Little's test)
    MAR  = Missing At Random (pattern associated with observed variables)
    MNAR = Missing Not At Random (pattern associated with unobserved values)

    "UNKNOWN" is the default before analysis. The detection engine will
    attempt to classify patterns but never claims certainty.
    """

    MCAR = "mcar"
    MAR = "mar"
    MNAR = "mnar"
    UNKNOWN = "unknown"
