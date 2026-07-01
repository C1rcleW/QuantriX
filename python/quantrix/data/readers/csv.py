"""CSV reader.

Reads CSV/TSV files into a Quantrix Dataset, with encoding auto-detection
and basic type inference from Polars dtype analysis.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.data.readers.base import (
    build_dataset,
    build_variable_metadata,
    enrich_metadata_from_data,
    variable_type_to_measure_level,
)


class CsvReader:
    """Read CSV/TSV files into a Quantrix Dataset.

    Implements ReaderProtocol structurally.

    Usage:
        reader = CsvReader()
        dataset = reader.read("path/to/data.csv")
    """

    format_name: str = "csv"
    format_extensions: list[str] = [".csv", ".tsv", ".txt"]

    def read(self, path: str, **kwargs: object) -> Dataset:
        """Read a CSV file and return a Dataset with inferred metadata."""
        path_obj = Path(path)

        # Determine separator from extension
        separator = "\t" if path_obj.suffix.lower() in (".tsv",) else ","

        # Merge kwargs with defaults
        options: dict[str, object] = {
            "separator": separator,
            "has_header": True,
            "null_values": ["", "NA", "N/A", "NULL", ".", "NaN"],
            "try_parse_dates": True,
            "truncate_ragged_lines": True,
            "encoding": "utf8-lossy",  # Tolerant of encoding errors
        }
        options.update(kwargs)

        # Read with Polars
        df = pl.read_csv(str(path_obj), **options)  # type: ignore[arg-type]

        # Build metadata
        variables = self._infer_variables(df)

        dataset = build_dataset(
            df=df,
            variables=variables,
            name=path_obj.stem,
            source_path=path_obj,
            source_format="csv",
        )

        # Enrich from data
        for var in dataset.variables:
            enrich_metadata_from_data(var, df[var.name])

        return dataset

    @staticmethod
    def _infer_variables(df: pl.DataFrame) -> list[VariableMetadata]:
        """Infer VariableMetadata from Polars DataFrame schema.

        This is a conservative inference: numeric → CONTINUOUS, string → STRING,
        boolean → NOMINAL. The full type inference engine (type_detector.py) will
        refine these based on cardinality and distribution later.
        """
        variables: list[VariableMetadata] = []

        for col_name in df.columns:
            dtype = df[col_name].dtype

            if dtype in (pl.Float64, pl.Float32) or dtype in (
                pl.Int64,
                pl.Int32,
                pl.Int16,
                pl.Int8,
            ):
                var_type = VariableType.CONTINUOUS
            elif dtype == pl.Boolean:
                var_type = VariableType.NOMINAL
            elif dtype in (pl.String, pl.Categorical, pl.Enum):
                var_type = VariableType.STRING
            else:
                var_type = VariableType.STRING

            var = build_variable_metadata(
                name=col_name,
                label=col_name,
                variable_type=var_type,
                measure_level=variable_type_to_measure_level(var_type),
                value_labels=[],
                format_name="csv",
            )
            variables.append(var)

        return variables
