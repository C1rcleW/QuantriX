"""SPSS .sav file reader.

Reads SPSS data files via pyreadstat, preserving all metadata:
- Variable names, labels, types
- Value labels
- Missing value definitions
- Measurement levels
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pyreadstat

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import MissingDefinition, VariableMetadata
from quantrix.core.types import MeasureLevel, VariableType
from quantrix.data.readers.base import (
    build_dataset,
    build_variable_metadata,
    enrich_metadata_from_data,
    spss_measure_to_measure_level,
    spss_measure_to_type,
    value_labels_from_spss,
)


class SpssReader:
    """Read SPSS .sav files into a Quantrix Dataset.

    Implements ReaderProtocol structurally.

    Usage:
        reader = SpssReader()
        dataset = reader.read("path/to/data.sav")
    """

    format_name: str = "sav"
    format_extensions: list[str] = [".sav", ".zsav"]

    def read(self, path: str) -> Dataset:
        """Read a .sav file and return a fully annotated Dataset."""
        path_obj = Path(path)

        # Read data and metadata in one pass
        pd_df, meta = pyreadstat.read_sav(
            filename_path=str(path_obj),
            encoding=None,  # Auto-detect encoding
            apply_value_formats=False,  # Keep raw values, labels are separate
        )

        # pyreadstat returns a pandas DataFrame; convert to Polars
        df = pl.from_pandas(pd_df)

        # Build variable metadata
        variables: list[VariableMetadata] = []
        for i, col_name in enumerate(meta.column_names):
            var_label = meta.column_labels[i] or ""
            measure = meta.variable_measure.get(col_name, "unknown")
            var_type = spss_measure_to_type(measure)
            measure_lvl = spss_measure_to_measure_level(measure)

            # Override for string variables: preserve storage type as STRING
            if df[col_name].dtype == pl.String:
                var_type = VariableType.STRING
                measure_lvl = MeasureLevel.NOMINAL

            val_labels = meta.variable_value_labels.get(col_name)
            value_lbls = value_labels_from_spss(val_labels)
            missing_def = self._extract_missing_definition(meta, col_name)

            var_meta = build_variable_metadata(
                name=col_name,
                label=var_label,
                variable_type=var_type,
                measure_level=measure_lvl,
                value_labels=value_lbls,
                format_name="sav",
            )
            var_meta.missing_definition = missing_def
            variables.append(var_meta)

        dataset = build_dataset(
            df=df,
            variables=variables,
            name=path_obj.stem,
            source_path=path_obj,
            source_format="sav",
        )

        for var in dataset.variables:
            enrich_metadata_from_data(var, df[var.name])

        return dataset

    @staticmethod
    def _extract_missing_definition(
        meta: pyreadstat.metadata_container, col_name: str
    ) -> MissingDefinition:
        """Extract SPSS missing value definitions for a single variable."""
        discrete: list[float] = []
        range_low: float | None = None
        range_high: float | None = None

        # Missing ranges (pyreadstat >=1.3 uses MissingRange objects)
        ranges = meta.missing_ranges.get(col_name, [])
        if ranges:
            for r in ranges:
                if hasattr(r, "lo") and hasattr(r, "hi"):
                    lo_val = float(r.lo) if r.lo is not None else None  # type: ignore[union-attr]
                    hi_val = float(r.hi) if r.hi is not None else None  # type: ignore[union-attr]
                    if lo_val == hi_val and lo_val is not None:
                        discrete.append(lo_val)
                    elif range_low is None:
                        range_low = lo_val
                        range_high = hi_val

        # Also check user-defined missing values (from read or older write paths)
        user_missing = meta.missing_user_values.get(col_name, [])
        for v in user_missing:
            if float(v) not in discrete:
                discrete.append(float(v))

        return MissingDefinition(
            discrete=discrete, range_low=range_low, range_high=range_high
        )
