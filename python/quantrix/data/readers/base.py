"""Base reader with shared utilities for all format readers.

Every format reader (SAV, CSV, XLSX, DTA) inherits from BaseReader
and implements ReaderProtocol.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import ValueLabel, VariableMetadata
from quantrix.core.types import MeasureLevel, VariableType

# ── SPSS measure level → Quantrix VariableType mapping ──────────────────

_SPSS_MEASURE_TO_TYPE: dict[str, VariableType] = {
    "scale": VariableType.CONTINUOUS,
    "ordinal": VariableType.ORDINAL,
    "nominal": VariableType.NOMINAL,
    "unknown": VariableType.NOMINAL,
}

# Polars dtype → VariableType mapping (for CSV and other format-less readers)
_POLARS_DTYPE_TO_TYPE: dict[pl.DataType, VariableType] = {
    pl.Float64: VariableType.CONTINUOUS,
    pl.Float32: VariableType.CONTINUOUS,
    pl.Int64: VariableType.CONTINUOUS,
    pl.Int32: VariableType.CONTINUOUS,
    pl.Int16: VariableType.CONTINUOUS,
    pl.Int8: VariableType.CONTINUOUS,
    pl.UInt64: VariableType.CONTINUOUS,
    pl.UInt32: VariableType.CONTINUOUS,
    pl.UInt16: VariableType.CONTINUOUS,
    pl.UInt8: VariableType.CONTINUOUS,
    pl.Boolean: VariableType.NOMINAL,
    pl.String: VariableType.STRING,
    pl.Categorical: VariableType.NOMINAL,
    pl.Enum: VariableType.NOMINAL,
}


def spss_measure_to_type(measure: str) -> VariableType:
    """Convert SPSS measure level string to Quantrix VariableType."""
    return _SPSS_MEASURE_TO_TYPE.get(measure.lower(), VariableType.NOMINAL)


def spss_measure_to_measure_level(measure: str) -> MeasureLevel:
    """Convert SPSS measure level to Stevens' measurement level."""
    mapping = {
        "scale": MeasureLevel.INTERVAL,
        "ordinal": MeasureLevel.ORDINAL,
        "nominal": MeasureLevel.NOMINAL,
    }
    return mapping.get(measure.lower(), MeasureLevel.NOMINAL)


def variable_type_to_measure_level(vt: VariableType) -> MeasureLevel:
    """Map VariableType to a sensible default MeasureLevel.

    Used when the source format doesn't provide measurement level (e.g., CSV).
    """
    mapping: dict[VariableType, MeasureLevel] = {
        VariableType.CONTINUOUS: MeasureLevel.INTERVAL,
        VariableType.ORDINAL: MeasureLevel.ORDINAL,
        VariableType.NOMINAL: MeasureLevel.NOMINAL,
        VariableType.STRING: MeasureLevel.NOMINAL,
    }
    return mapping.get(vt, MeasureLevel.NOMINAL)


def value_labels_from_spss(
    labels: dict[int | float, str] | None,
) -> list[ValueLabel]:
    """Convert pyreadstat value_labels dict to Quantrix ValueLabel list."""
    if not labels:
        return []
    return [
        ValueLabel(value=k, label=v, source="original")
        for k, v in sorted(labels.items(), key=lambda x: str(x[0]))
    ]


def build_variable_metadata(
    name: str,
    label: str,
    variable_type: VariableType,
    measure_level: MeasureLevel,
    value_labels: list[ValueLabel],
    format_name: str,
) -> VariableMetadata:
    """Build a VariableMetadata instance with sensible defaults."""
    return VariableMetadata(
        name=name,
        label=label or name,
        variable_type=variable_type,
        measure_level=measure_level,
        value_labels=value_labels,
        source_format=format_name,
    )


def enrich_metadata_from_data(meta: VariableMetadata, column: pl.Series) -> VariableMetadata:
    """Populate statistical summaries from the actual data column.

    Called after the Dataset is built, this fills in n_valid, missing_count,
    basic distribution stats, etc.
    """
    valid_series = column.drop_nulls()
    total = len(column)
    valid = len(valid_series)

    meta.n_valid = valid
    meta.missing_count = total - valid
    meta.missing_percentage = (total - valid) / total * 100 if total > 0 else 0.0
    meta.n_unique = valid_series.n_unique() if valid > 0 else 0

    if meta.variable_type == VariableType.CONTINUOUS and valid > 0:
        meta.min_value = valid_series.min()
        meta.max_value = valid_series.max()
        meta.mean = valid_series.mean()
        meta.std_dev = valid_series.std()
        # Skewness and kurtosis require scipy; populated by inference engine

    return meta


def build_dataset(
    df: pl.DataFrame,
    variables: list[VariableMetadata],
    name: str,
    source_path: Path,
    source_format: str,
) -> Dataset:
    """Construct a Dataset from DataFrame and metadata."""
    return Dataset(
        name=name,
        label=name,
        source_path=source_path,
        source_format=source_format,
        n_rows=df.height,
        n_columns=df.width,
        variables=variables,
        data=df,
    )
