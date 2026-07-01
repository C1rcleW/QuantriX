"""Tests for the TypeDetector."""

import polars as pl
import pytest

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.data.inference.type_detector import (
    TypeDetector,
    refine_variable_types,
    suggest_ordinal_from_labels,
)


class TestTypeDetector:
    """Type inference refinement tests."""

    @pytest.fixture
    def detector(self):
        return TypeDetector()

    def test_float_always_continuous(self, detector):
        df = pl.DataFrame({"x": [1.5, 2.3, 3.7]})
        var = VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS)
        detector.refine([var], df)
        assert var.variable_type == VariableType.CONTINUOUS

    def test_bool_always_nominal(self, detector):
        df = pl.DataFrame({"x": [True, False, True]})
        var = VariableMetadata(name="x", variable_type=VariableType.NOMINAL)
        detector.refine([var], df)
        assert var.variable_type == VariableType.NOMINAL

    def test_low_cardinality_int_becomes_nominal(self, detector):
        df = pl.DataFrame({"x": [1, 2, 1, 2, 1]})
        var = VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS)
        detector.refine([var], df)
        assert var.variable_type == VariableType.NOMINAL  # 2 unique

    def test_mid_cardinality_int_becomes_ordinal(self, detector):
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3]})
        var = VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS)
        detector.refine([var], df)
        assert var.variable_type == VariableType.ORDINAL

    def test_high_cardinality_int_stays_continuous(self, detector):
        df = pl.DataFrame({"x": list(range(100))})
        var = VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS)
        detector.refine([var], df)
        assert var.variable_type == VariableType.CONTINUOUS

    def test_low_cardinality_str_becomes_nominal(self, detector):
        df = pl.DataFrame({"x": ["A", "B", "A", "B", "A"]})
        var = VariableMetadata(name="x", variable_type=VariableType.STRING)
        detector.refine([var], df)
        assert var.variable_type == VariableType.NOMINAL

    def test_high_cardinality_str_stays_string(self, detector):
        df = pl.DataFrame({"x": [f"text_{i}" for i in range(100)]})
        var = VariableMetadata(name="x", variable_type=VariableType.STRING)
        detector.refine([var], df)
        assert var.variable_type == VariableType.STRING

    def test_refine_does_not_modify_unknown_column(self, detector):
        var = VariableMetadata(name="missing", variable_type=VariableType.CONTINUOUS)
        df = pl.DataFrame({"other": [1, 2, 3]})
        detector.refine([var], df)
        assert var.variable_type == VariableType.CONTINUOUS  # unchanged

    def test_convenience_function(self):
        df = pl.DataFrame({"x": [1, 2, 1, 2, 1]})
        vars_list = [
            VariableMetadata(name="x", variable_type=VariableType.CONTINUOUS),
        ]
        refined = refine_variable_types(vars_list, df)
        assert refined[0].variable_type == VariableType.NOMINAL


class TestSuggestOrdinalFromLabels:
    """Value-label-based ordinal detection."""

    def test_labeled_likert_becomes_ordinal(self):
        from quantrix.core.metadata import ValueLabel

        var = VariableMetadata(
            name="satisfaction",
            variable_type=VariableType.NOMINAL,
            value_labels=[
                ValueLabel(value=1, label="Very Dissatisfied"),
                ValueLabel(value=2, label="Dissatisfied"),
                ValueLabel(value=3, label="Neutral"),
                ValueLabel(value=4, label="Satisfied"),
                ValueLabel(value=5, label="Very Satisfied"),
            ],
        )
        suggest_ordinal_from_labels([var])
        assert var.variable_type == VariableType.ORDINAL

    def test_unordered_labels_remain_nominal(self):
        from quantrix.core.metadata import ValueLabel

        var = VariableMetadata(
            name="region",
            variable_type=VariableType.NOMINAL,
            value_labels=[
                ValueLabel(value=1, label="North"),
                ValueLabel(value=3, label="South"),
                ValueLabel(value=2, label="East"),
            ],
        )
        suggest_ordinal_from_labels([var])
        assert var.variable_type == VariableType.NOMINAL

    def test_too_few_labels_remain_nominal(self):
        from quantrix.core.metadata import ValueLabel

        var = VariableMetadata(
            name="gender",
            variable_type=VariableType.NOMINAL,
            value_labels=[
                ValueLabel(value=1, label="Male"),
                ValueLabel(value=2, label="Female"),
            ],
        )
        suggest_ordinal_from_labels([var])
        assert var.variable_type == VariableType.NOMINAL  # only 2 labels
