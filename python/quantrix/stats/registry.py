"""Stat method registry — maps method names to implementations.

Usage:
    registry = get_registry()
    result = registry["independent_ttest"].execute(dataset, dv, ivs)
"""

from __future__ import annotations

from quantrix.stats.base import BaseStatMethod
from quantrix.stats.comparison import (
    IndependentTTest,
    MannWhitney,
    OneWayANOVA,
    KruskalWallis,
)
from quantrix.stats.correlation import ChiSquare, PearsonCorrelation, SpearmanCorrelation
from quantrix.stats.descriptive import Descriptives, Frequencies
from quantrix.stats.regression import LinearRegression

_registry: dict[str, BaseStatMethod] = {}


def get_registry() -> dict[str, BaseStatMethod]:
    if not _registry:
        _register_all()
    return _registry


def _register_all():
    methods = [
        Frequencies(),
        Descriptives(),
        IndependentTTest(),
        OneWayANOVA(),
        MannWhitney(),
        KruskalWallis(),
        PearsonCorrelation(),
        SpearmanCorrelation(),
        ChiSquare(),
        LinearRegression(),
    ]
    for m in methods:
        _registry[m.method_name] = m


def execute_analysis(
    method_name: str, dataset, dv, ivs, **params
) -> dict:
    """Execute a statistical analysis and return results as dict.

    Args:
        method_name: "independent_ttest", "pearson_correlation", etc.
        dataset: Quantrix Dataset.
        dv: Dependent VariableMetadata.
        ivs: List of independent VariableMetadata.

    Returns:
        Dict with statistics, tables, and interpretation fields.
    """
    registry = get_registry()
    method = registry.get(method_name)
    if method is None:
        return {"errors": [f"Unknown method: {method_name}"]}

    try:
        result = method.execute(dataset, dv, ivs, **params)
        return result.to_dict()
    except Exception as e:
        return {"errors": [f"Execution failed: {e}"]}
