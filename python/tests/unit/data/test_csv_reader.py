"""Tests for the CSV reader."""

import pytest

from quantrix.core.types import VariableType
from quantrix.data.readers.csv import CsvReader


class TestCsvReader:
    """CSV reader tests using a synthetic CSV file."""

    @pytest.fixture(autouse=True)
    def setup(self, csv_file_path):
        self.reader = CsvReader()
        self.dataset = self.reader.read(str(csv_file_path))

    def test_dataset_shape(self):
        assert self.dataset.n_rows == 20
        assert self.dataset.n_columns == 4

    def test_source_format(self):
        assert self.dataset.source_format == "csv"

    def test_variable_names(self):
        assert self.dataset.variable_names == ["id", "score", "group", "passed"]

    def test_numeric_typed_as_continuous(self):
        score = self.dataset.get_variable("score")
        assert score.variable_type == VariableType.CONTINUOUS

    def test_string_typed_as_string(self):
        group = self.dataset.get_variable("group")
        assert group.variable_type == VariableType.STRING

    def test_boolean_typed_as_nominal(self):
        passed = self.dataset.get_variable("passed")
        assert passed.variable_type == VariableType.NOMINAL

    def test_missing_values_detected(self):
        score = self.dataset.get_variable("score")
        # We have 2 None values in the test data
        assert score.missing_count == 2
        assert score.n_valid == 18

    def test_n_unique_for_categorical(self):
        group = self.dataset.get_variable("group")
        assert group.n_unique == 2

    def test_distribution_stats_for_continuous(self):
        score = self.dataset.get_variable("score")
        assert score.mean is not None
        assert score.min_value is not None
        assert score.max_value is not None
        assert 60.0 < score.mean < 100.0
