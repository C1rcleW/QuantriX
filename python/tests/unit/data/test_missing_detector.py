"""Tests for the MissingDetector."""

import polars as pl
import pytest

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import MissingPattern
from quantrix.data.inference.missing_detector import MissingDetector


class TestMissingDetector:
    """Missing value detection tests."""

    @pytest.fixture
    def detector(self):
        return MissingDetector()

    def test_no_missing(self, detector):
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        vars_list = [
            VariableMetadata(name="a"),
            VariableMetadata(name="b"),
        ]
        detector.analyze(vars_list, df)
        for v in vars_list:
            assert v.missing_count == 0
            assert v.missing_percentage == 0.0
            assert v.n_valid == 3

    def test_partial_missing(self, detector):
        df = pl.DataFrame({
            "x": [1, None, 3, None, 5],
            "y": [1.0, 2.0, None, 4.0, 5.0],
        })
        vars_list = [
            VariableMetadata(name="x"),
            VariableMetadata(name="y"),
        ]
        detector.analyze(vars_list, df)
        assert vars_list[0].missing_count == 2
        assert vars_list[0].missing_percentage == 40.0
        assert vars_list[0].n_valid == 3
        assert vars_list[1].missing_count == 1
        assert vars_list[1].missing_percentage == 20.0

    def test_moderate_missing_classified_as_mar(self, detector):
        df = pl.DataFrame({"a": [1, 2, 3, 4, 5, 6, 7, 8, 9, None]})
        vars_list = [VariableMetadata(name="a")]
        detector.analyze(vars_list, df)
        # 10% missing → moderate rate, classified as MAR
        assert vars_list[0].missing_pattern == MissingPattern.MAR

    def test_high_missing_classified_as_mnar(self, detector):
        df = pl.DataFrame({
            "a": [1, None, None, None, None],  # 80% missing
        })
        vars_list = [VariableMetadata(name="a")]
        detector.analyze(vars_list, df)
        assert vars_list[0].missing_pattern == MissingPattern.MNAR

    def test_summary_table(self, detector):
        df = pl.DataFrame({"a": [1, None, 3], "b": [None, 2.0, 3.0]})
        vars_list = [
            VariableMetadata(name="a"),
            VariableMetadata(name="b"),
        ]
        detector.analyze(vars_list, df)
        summary = detector.missing_summary_table(vars_list)
        assert len(summary) == 2
        assert summary[0]["missing_count"] == 1
        assert summary[1]["missing_count"] == 1

    def test_case_missing_counts(self, detector):
        df = pl.DataFrame({
            "a": [1, None, None],
            "b": [None, 2.0, None],
        })
        result = detector.case_missing_counts(df)
        assert result["missing_count"].to_list() == [1, 1, 2]

    def test_empty_dataset(self, detector):
        df = pl.DataFrame({})
        vars_list: list[VariableMetadata] = []
        detector.analyze(vars_list, df)
        assert vars_list == []
