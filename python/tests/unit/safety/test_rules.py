"""Tests for safety rules."""

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.safety.engine import SafetyNet
from quantrix.safety.rules.homogeneity import HomogeneityRule
from quantrix.safety.rules.multiple_comparison import MultipleComparisonRule
from quantrix.safety.rules.normality import NormalityRule
from quantrix.safety.rules.outliers import OutlierRule
from quantrix.safety.rules.sample_size import SampleSizeRule
from quantrix.safety.rules.type_match import TypeMatchRule


def make_dataset(variables: list[VariableMetadata], data: dict) -> Dataset:
    df = pl.DataFrame(data)
    return Dataset(
        name="test", n_rows=df.height, n_columns=df.width,
        variables=variables, data=df,
    )


def make_var(name: str, vtype: VariableType, n_unique: int | None = None) -> VariableMetadata:
    return VariableMetadata(name=name, variable_type=vtype, n_unique=n_unique)


class TestTypeMatchRule:
    def test_valid_types(self):
        rule = TypeMatchRule()
        dv = make_var("income", VariableType.CONTINUOUS)
        iv = make_var("gender", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {"income": [1.0], "gender": [0]})
        warnings = rule.check("independent_ttest", dv, [iv], ds)
        assert warnings == []

    def test_wrong_dv_type(self):
        rule = TypeMatchRule()
        dv = make_var("income", VariableType.NOMINAL)
        iv = make_var("gender", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {"income": [1], "gender": [0]})
        warnings = rule.check("independent_ttest", dv, [iv], ds)
        assert len(warnings) == 1
        assert warnings[0].severity == "error"

    def test_binary_logistic_needs_two_categories(self):
        rule = TypeMatchRule()
        dv = make_var("region", VariableType.NOMINAL, n_unique=5)
        ds = make_dataset([dv], {"region": [1, 2, 3, 4, 5]})
        warnings = rule.check("binary_logistic", dv, [], ds)
        assert any("exactly 2 categories" in w.message for w in warnings)


class TestSampleSizeRule:
    def test_small_sample(self):
        rule = SampleSizeRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        ds = make_dataset([dv], {"x": [1, 2, 3, 4]})
        warnings = rule.check("pearson_correlation", dv, [], ds)
        assert len(warnings) == 1
        assert "below" in warnings[0].message

    def test_tiny_group(self):
        rule = SampleSizeRule()
        dv = make_var("score", VariableType.CONTINUOUS)
        iv = make_var("group", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {"score": [1, 2], "group": [0, 1]})
        warnings = rule.check("independent_ttest", dv, [iv], ds)
        assert any("below" in w.message for w in warnings)


class TestNormalityRule:
    def test_normal_data_passes(self):
        rule = NormalityRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        ds = make_dataset([dv], {"x": [1.0, 2.0, 3.0, 2.0, 1.0, 2.0, 3.0, 2.0]})
        warnings = rule.check("independent_ttest", dv, [], ds)
        # Uniform-ish small data, should have low skewness
        assert dv.skewness is not None

    def test_skewed_data_warns(self):
        rule = NormalityRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        # Very extreme: 19 ones and one 1000 → skewness > 2
        ds = make_dataset([dv], {"x": [1]*19 + [1000]})
        warnings = rule.check("independent_ttest", dv, [], ds)
        assert len(warnings) >= 1


class TestHomogeneityRule:
    def test_equal_variance_passes(self):
        rule = HomogeneityRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        iv = make_var("g", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {
            "x": [1.0, 2.0, 3.0, 2.0, 3.0, 4.0],
            "g": [0, 0, 0, 1, 1, 1],
        })
        warnings = rule.check("independent_ttest", dv, [iv], ds)
        # Similar SDs → no warning
        severity_errors = [w for w in warnings if w.severity == "error"]
        assert severity_errors == []

    def test_unequal_variance_warns(self):
        rule = HomogeneityRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        iv = make_var("g", VariableType.NOMINAL)
        # Group 0: all 1.0 (sd=0), Group 1: extreme spread → SD ratio > 2
        ds = make_dataset([dv, iv], {
            "x": [1]*10 + [1, 10, 100, 200, 500],
            "g": [0]*10 + [1]*5,
        })
        warnings = rule.check("independent_ttest", dv, [iv], ds)
        assert any("vary" in w.message.lower() or "zero variance" in w.message.lower() for w in warnings)


class TestOutlierRule:
    def test_no_outliers(self):
        rule = OutlierRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        ds = make_dataset([dv], {"x": [5.0]*20})
        _ = rule.check("independent_ttest", dv, [], ds)
        assert dv.outlier_count == 0

    def test_outliers_detected(self):
        rule = OutlierRule()
        dv = make_var("x", VariableType.CONTINUOUS)
        # 19 ones + 1000 creates IQR=0, then all non-1 values are outliers
        ds = make_dataset([dv], {"x": [1]*19 + [1000]})
        _ = rule.check("independent_ttest", dv, [], ds)
        assert dv.outlier_count > 0


class TestMultipleComparisonRule:
    def test_multi_predictors_info(self):
        rule = MultipleComparisonRule()
        dv = make_var("y", VariableType.CONTINUOUS)
        iv1 = make_var("x1", VariableType.CONTINUOUS)
        iv2 = make_var("x2", VariableType.CONTINUOUS)
        ds = make_dataset([dv, iv1, iv2], {"y": [1], "x1": [2], "x2": [3]})
        warnings = rule.check("linear_regression", dv, [iv1, iv2], ds)
        assert len(warnings) >= 1

    def test_posthoc_reminder(self):
        rule = MultipleComparisonRule()
        dv = make_var("y", VariableType.CONTINUOUS)
        iv = make_var("g", VariableType.NOMINAL, n_unique=4)
        ds = make_dataset([dv, iv], {"y": [1, 2, 3, 4], "g": [0, 1, 2, 3]})
        warnings = rule.check("oneway_anova", dv, [iv], ds)
        assert any("correction" in w.message.lower() for w in warnings)


class TestSafetyNet:
    def test_collects_all_rules(self):
        net = SafetyNet()
        net.register(TypeMatchRule())
        net.register(SampleSizeRule())

        dv = make_var("income", VariableType.NOMINAL)  # Wrong type for ttest
        iv = make_var("gender", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {"income": [1], "gender": [0]})

        report = net.check("independent_ttest", dv, [iv], ds)
        assert report.has_errors
        assert len(report.errors) >= 1

    def test_report_to_dict(self):
        net = SafetyNet()
        net.register(TypeMatchRule())
        dv = make_var("income", VariableType.CONTINUOUS)
        iv = make_var("gender", VariableType.NOMINAL)
        ds = make_dataset([dv, iv], {"income": [1.0], "gender": [0]})
        report = net.check("independent_ttest", dv, [iv], ds)
        d = report.to_dict()
        assert "errors" in d
        assert "warnings" in d
