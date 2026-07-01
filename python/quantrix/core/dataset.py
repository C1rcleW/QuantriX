"""Dataset — the central data model of Quantrix.

A Dataset wraps a Polars DataFrame with typed variable metadata.
Every module reads from Dataset; every reader produces one.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from quantrix.core.metadata import VariableMetadata


class Dataset(BaseModel):
    """A rectangular dataset with full variable-level metadata.

    The actual data is stored as a Polars DataFrame. The Pydantic model
    carries metadata and provenance. For serialization (e.g., API responses),
    the data is JSON-ified separately.

    Design constraint: Dataset is immutable. Any transformation produces
    a new Dataset with updated provenance.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Identity
    name: str = ""
    label: str = ""
    source_path: Path | None = None
    source_format: str = ""  # "sav", "csv", "xlsx", "dta"

    # Shape
    n_rows: int = 0
    n_columns: int = 0

    # Variables (ordered as they appear in the data)
    variables: list[VariableMetadata] = Field(default_factory=list)

    # Data (Polars DataFrame — excluded from JSON serialization)
    data: object | None = Field(default=None, exclude=True)

    # Provenance
    imported_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def variable_names(self) -> list[str]:
        """Convenience accessor for variable name list."""
        return [v.name for v in self.variables]

    def get_variable(self, name: str) -> VariableMetadata:
        """Look up a variable by name. Raises KeyError if not found."""
        for var in self.variables:
            if var.name == name:
                return var
        raise KeyError(f"Variable '{name}' not found in dataset '{self.name}'")

    def get_variables_by_type(self, variable_type: str) -> list[VariableMetadata]:
        """Filter variables by type (continuous, ordinal, nominal, string)."""
        return [v for v in self.variables if v.variable_type.value == variable_type]
