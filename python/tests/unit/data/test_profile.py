"""Tests for the DataProfile generator."""

import polars as pl
import pytest

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import ValueLabel, VariableMetadata
from quantrix.core.types import VariableType
from quantrix.data.profile import ProfileGenerator


class TestProfileGenerator:
    """Data profile generation tests."""

    @pytest.fixture
    def generator(self):
        return ProfileGenerator()

    @pytest.fixture
    def sample_dataset(self):
        df = pl.DataFrame(
            {
                "age": [25, 30, 35, None, 45],
                "gender": [1, 2, 1, 2, 1],
                "score": [85.5, 92.0, 78.3, 88.1, None],
                "city": ["Beijing", "Shanghai", "Beijing", None, "Chengdu"],
            }
        )
        gender_labels = [
            ValueLabel(value=1, label="Male"),
            ValueLabel(value=2, label="Female"),
        ]
        variables = [
            VariableMetadata(
                name="age",
                label="Age",
                variable_type=VariableType.CONTINUOUS,
                n_valid=4,
                missing_count=1,
                n_unique=4,
                min_value=25.0,
                max_value=45.0,
                mean=33.75,
                std_dev=7.5,
            ),
            VariableMetadata(
                name="gender",
                label="Gender",
                variable_type=VariableType.NOMINAL,
                n_valid=5,
                missing_count=0,
                n_unique=2,
                value_labels=gender_labels,
            ),
            VariableMetadata(
                name="score",
                label="Test Score",
                variable_type=VariableType.CONTINUOUS,
                n_valid=4,
                missing_count=1,
                n_unique=4,
                min_value=78.3,
                max_value=92.0,
                mean=85.975,
                std_dev=5.0,
            ),
            VariableMetadata(
                name="city",
                label="City",
                variable_type=VariableType.STRING,
                n_valid=4,
                missing_count=1,
                n_unique=3,
            ),
        ]
        return Dataset(
            name="test",
            source_format="csv",
            n_rows=5,
            n_columns=4,
            variables=variables,
            data=df,
        )

    def test_profile_structure(self, generator, sample_dataset):
        profile = generator.generate(sample_dataset)
        assert profile.dataset_name == "test"
        assert profile.n_rows == 5
        assert profile.n_columns == 4
        assert profile.source_format == "csv"

    def test_variable_profiles_count(self, generator, sample_dataset):
        profile = generator.generate(sample_dataset)
        assert len(profile.variable_profiles) == 4

    def test_completeness_stats(self, generator, sample_dataset):
        profile = generator.generate(sample_dataset)
        # age missing 1, score missing 1, city missing 1 → 3 missing cells
        assert profile.total_missing_cells == 3
        # 3/20 = 15%
        assert profile.overall_missing_rate == pytest.approx(15.0, abs=0.1)

    def test_quality_flags(self, generator, sample_dataset):
        profile = generator.generate(sample_dataset)
        # age has 20% missing → high_missing
        assert profile.has_high_missing is False  # 20% exactly is not "high"
        assert profile.has_constant_variables is False

    def test_markdown_output(self, generator, sample_dataset):
        md = generator.generate(sample_dataset).to_markdown()
        assert "# Data Profile: test" in md
        assert "Rows**: 5" in md
        assert "age" in md
        assert "gender" in md
        # Value labels should appear
        assert "Male" in md

    def test_constant_variable_detected(self, generator):
        df = pl.DataFrame({"x": [1, 1, 1, 1, 1]})
        var = VariableMetadata(
            name="x",
            variable_type=VariableType.CONTINUOUS,
            n_valid=5,
            missing_count=0,
            n_unique=1,
        )
        ds = Dataset(name="test", n_rows=5, n_columns=1, variables=[var], data=df)
        profile = generator.generate(ds)
        assert profile.has_constant_variables is True

    def test_high_missing_detected(self, generator):
        df = pl.DataFrame({"x": [1, None, None, None, None]})
        var = VariableMetadata(
            name="x",
            variable_type=VariableType.CONTINUOUS,
            n_valid=1,
            missing_count=4,
            n_unique=1,
        )
        ds = Dataset(name="test", n_rows=5, n_columns=1, variables=[var], data=df)
        profile = generator.generate(ds)
        assert profile.has_high_missing is True

    def test_empty_dataset(self, generator):
        ds = Dataset(name="empty")
        profile = generator.generate(ds)
        assert profile.n_rows == 0
        assert profile.n_columns == 0
        assert profile.total_missing_cells == 0
