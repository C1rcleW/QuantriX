"""Base class for all statistical methods.

Every stat method inherits from BaseStatMethod and implements execute().
The base class handles common patterns: data extraction, null handling,
and result formatting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata


@dataclass
class StatResult:
    def __init__(self, **kwargs):
        known = {f.name for f in self.__dataclass_fields__.values()}
        for k, v in kwargs.items():
            if k in known:
                setattr(self, k, v)
            else:
                self.misc[k] = v
        if not hasattr(self, "statistics"):
            self.statistics = {}
        if not hasattr(self, "effect_sizes"):
            self.effect_sizes = {}
        if not hasattr(self, "tables"):
            self.tables = []
        if not hasattr(self, "errors"):
            self.errors = []
        if not hasattr(self, "group_labels"):
            self.group_labels = []

    """Internal result container. Mapped to AnalysisResult in the API layer."""

    method_name: str
    method_family: str
    n_samples: int

    statistics: dict[str, float] = field(default_factory=dict)
    effect_sizes: dict[str, float] = field(default_factory=dict)
    tables: list[dict] = field(default_factory=list)

    # Interpretation-ready fields
    dv_label: str = ""
    iv_label: str = ""
    group_labels: list[str] = field(default_factory=list)
    sig_text: str = ""
    effect_size_text: str = ""

    errors: list[str] = field(default_factory=list)
    misc: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "method_name": self.method_name,
            "method_family": self.method_family,
            "n_samples": self.n_samples,
            "statistics": self.statistics,
            "effect_sizes": self.effect_sizes,
            "tables": self.tables,
            "dv_label": self.dv_label,
            "iv_label": self.iv_label,
            "group_labels": self.group_labels,
            "sig_text": self.sig_text,
            "effect_size_text": self.effect_size_text,
            "errors": self.errors,
        }


class BaseStatMethod:
    """Base for all statistical methods."""

    method_name: str = "base"
    method_family: str = "base"

    def execute(
        self,
        dataset: Dataset,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata] | None = None,
        **params: object,
    ) -> StatResult:
        raise NotImplementedError

    def _get_column(self, dataset: Dataset, var: VariableMetadata) -> pl.Series:
        """Extract a valid column, dropping nulls for the variable."""
        if dataset.data is None or var.name not in dataset.data.columns:
            raise ValueError(f"Variable '{var.name}' not found in dataset")
        col = dataset.data[var.name]
        return col

    def _get_valid(self, dataset: Dataset, var: VariableMetadata) -> pl.Series:
        """Get valid (non-null) values for a variable."""
        return self._get_column(dataset, var).drop_nulls()

    @staticmethod
    def _format_p(p_value: float, alpha: float = 0.05) -> str:
        """Format p-value for display."""
        if p_value < 0.001:
            return "p < .001"
        return f"p = {p_value:.3f}"

    @staticmethod
    def _is_significant(p_value: float, alpha: float = 0.05) -> bool:
        return p_value < alpha

    @staticmethod
    def _cohens_d(mean1: float, mean2: float, sd1: float, sd2: float, n1: int, n2: int) -> float:
        """Cohen's d for independent groups with pooled SD."""
        pooled_sd = (((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2)) ** 0.5
        if pooled_sd == 0:
            return 0.0
        return abs(mean1 - mean2) / pooled_sd

    @staticmethod
    def _cohens_d_interpretation(d: float) -> str:
        d_abs = abs(d)
        if d_abs < 0.2:
            return "negligible"
        elif d_abs < 0.5:
            return "small"
        elif d_abs < 0.8:
            return "medium"
        else:
            return "large"
