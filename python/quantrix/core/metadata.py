"""Variable metadata model.

The richest struct in Quantrix. Mirrors SPSS variable view but adds
AI-inferred fields and data-quality markers that SPSS lacks.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, computed_field

from quantrix.core.types import MeasureLevel, MissingPattern, VariableType


class ValueLabel(BaseModel):
    """A single value-to-label mapping (e.g., 1 → "Male", 2 → "Female")."""

    value: int | float | str
    label: str
    source: str = "original"  # "original" (from file) or "inferred" (by AI)


class MissingDefinition(BaseModel):
    """How missing values are encoded for a variable.

    SPSS supports three kinds of missing definitions:
    - Discrete values: 99, 999
    - Range: -1 through 0
    - Range plus discrete: LO through 0, plus 999
    """

    discrete: list[float] = Field(default_factory=list)
    range_low: float | None = None
    range_high: float | None = None


class VariableMetadata(BaseModel):
    """Complete metadata for a single variable.

    This is the unit of transfer between Data Layer and all other modules.
    Every statistical method receives a list of VariableMetadata alongside
    the raw data to make informed decisions.
    """

    # Identity
    name: str
    label: str = ""

    # Type classification
    variable_type: VariableType = VariableType.NOMINAL
    measure_level: MeasureLevel = MeasureLevel.NOMINAL

    # Value decoding
    value_labels: list[ValueLabel] = Field(default_factory=list)

    # Missing value handling
    missing_definition: MissingDefinition = Field(default_factory=MissingDefinition)
    missing_count: int = 0
    missing_percentage: float = 0.0
    missing_pattern: MissingPattern = MissingPattern.UNKNOWN

    # Data quality markers (populated by inference engine)
    n_valid: int = 0
    n_unique: int | None = None
    outlier_count: int = 0

    # Distribution summary (for quick visual thumbnails)
    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None
    std_dev: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None

    # History
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_format: str = ""  # "sav", "csv", etc.

    @computed_field
    @property
    def is_complete(self) -> bool:
        """True if the variable has no missing values."""
        return self.missing_count == 0

    @computed_field
    @property
    def is_categorical(self) -> bool:
        """True for nominal, ordinal, or string types."""
        return self.variable_type in (
            VariableType.NOMINAL,
            VariableType.ORDINAL,
            VariableType.STRING,
        )

    @computed_field
    @property
    def is_continuous(self) -> bool:
        """True for continuous (scale) variables."""
        return self.variable_type == VariableType.CONTINUOUS

    @computed_field
    @property
    def display_name(self) -> str:
        """Human-readable name: label if present, otherwise variable name."""
        return self.label if self.label else self.name
