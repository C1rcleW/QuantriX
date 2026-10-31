"""Integration tests for the statistics engine."""

import polars as pl

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.stats.registry import execute_analysis, get_registry


def make_ds(data: dict) -> Dataset:
    df = pl.DataFrame(data)
    vars_list = []
    for name in df.columns:
        dtype = df[name].dtype
        vt = VariableType.CONTINUOUS
        if dtype in (pl.String, pl.Categorical):
            vt = VariableType.STRING
        elif dtype == pl.Boolean:
            vt = VariableType.NOMINAL
        elif dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8):
            n_unique = df[name].n_unique()
            vt = VariableType.NOMINAL if n_unique <= 2 else VariableType.CONTINUOUS
        vars_list.append(
            VariableMetadata(name=name, variable_type=vt, n_valid=len(df) - df[name].null_count())
        )
    return Dataset(name="test", n_rows=df.height, n_columns=df.width, variables=vars_list, data=df)


def get_var(ds, name):
    return ds.get_variable(name)


class TestDescriptive:
    def test_frequencies(self):
        ds = make_ds({"gender": [1, 2, 1, 1, 2, 1, 2, 1]})
        dv = get_var(ds, "gender")
        dv.variable_type = VariableType.NOMINAL
        r = execute_analysis("frequencies", ds, dv, [])
        assert r["errors"] == []
        assert r["statistics"]["n_total"] == 8
        assert "n_categories" in r["statistics"]

    def test_descriptives(self):
        ds = make_ds({"income": [50000, 60000, 45000, 75000, 55000]})
        dv = get_var(ds, "income")
        r = execute_analysis("descriptives", ds, dv, [])
        assert r["errors"] == []
        assert 40000 < r["statistics"]["mean"] < 80000


class TestComparison:
    def test_ttest(self):
        ds = make_ds(
            {
                "score": [85, 90, 78, 92, 88, 76, 82, 95, 80, 87],
                "group": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            }
        )
        dv = get_var(ds, "score")
        iv = get_var(ds, "group")
        iv.variable_type = VariableType.NOMINAL
        r = execute_analysis("independent_ttest", ds, dv, [iv])
        assert r["errors"] == []
        assert "t_stat" in r["statistics"]
        assert "p_value" in r["statistics"]
        assert "cohens_d" in r["effect_sizes"]

    def test_anova(self):
        ds = make_ds(
            {
                "score": [85, 90, 78, 82, 80, 70, 72, 68, 75, 88, 92, 95],
                "group": [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2],
            }
        )
        dv = get_var(ds, "score")
        iv = get_var(ds, "group")
        iv.variable_type = VariableType.NOMINAL
        iv.n_unique = 3
        r = execute_analysis("oneway_anova", ds, dv, [iv])
        assert r["errors"] == []
        assert "f_stat" in r["statistics"]

    def test_mann_whitney(self):
        ds = make_ds(
            {"rank": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "group": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]}
        )
        dv = get_var(ds, "rank")
        iv = get_var(ds, "group")
        iv.variable_type = VariableType.NOMINAL
        r = execute_analysis("mann_whitney", ds, dv, [iv])
        assert r["errors"] == []
        assert "u_stat" in r["statistics"]


class TestCorrelation:
    def test_pearson(self):
        import numpy as np

        rng = np.random.default_rng(42)
        x = rng.normal(0, 1, 50)
        y = x * 0.8 + rng.normal(0, 0.3, 50)
        ds = make_ds({"x": x, "y": y})
        dv = get_var(ds, "y")
        iv = get_var(ds, "x")
        r = execute_analysis("pearson_correlation", ds, dv, [iv])
        assert r["errors"] == []
        assert r["statistics"]["r"] > 0.5  # strong positive

    def test_chi_square(self):
        ds = make_ds(
            {
                "gender": [1, 1, 2, 2, 1, 1, 2, 2, 1, 2, 1, 2],
                "passed": [1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0],
            }
        )
        dv = get_var(ds, "passed")
        dv.variable_type = VariableType.NOMINAL
        iv = get_var(ds, "gender")
        iv.variable_type = VariableType.NOMINAL
        r = execute_analysis("chi_square", ds, dv, [iv])
        assert r["errors"] == []
        assert "chi_squared" in r["statistics"]


class TestRegression:
    def test_linear(self):
        import numpy as np

        rng = np.random.default_rng(42)
        x = rng.normal(50, 10, 30)
        y = x * 100 + 20000 + rng.normal(0, 5000, 30)
        ds = make_ds({"income": y, "education": x})
        dv = get_var(ds, "income")
        iv = get_var(ds, "education")
        r = execute_analysis("linear_regression", ds, dv, [iv])
        assert r["errors"] == []
        assert "r_squared" in r["statistics"]

    def test_linear_with_categorical_predictor(self):
        ds = make_ds(
            {
                "income": [50000, 61000, 45000, 72000, 55000, 48000],
                "gender": ["male", "female", "male", "female", "male", "female"],
            }
        )
        dv = get_var(ds, "income")
        iv = get_var(ds, "gender")
        iv.variable_type = VariableType.NOMINAL
        r = execute_analysis("linear_regression", ds, dv, [iv])
        assert r["errors"] == []
        rows = r["tables"][0]["rows"]
        assert len(rows) == 2
        assert any("gender" in str(row[0]).lower() for row in rows[1:])
        assert r["charts"][0]["chart_type"] == "box"

    def test_linear_with_multiple_predictors(self):
        ds = make_ds(
            {
                "income": [50000, 61000, 45000, 72000, 55000, 48000, 64000, 53000],
                "education": [12, 16, 9, 18, 14, 11, 17, 13],
                "age": [25, 31, 22, 45, 38, 29, 41, 34],
            }
        )
        dv = get_var(ds, "income")
        r = execute_analysis(
            "linear_regression",
            ds,
            dv,
            [get_var(ds, "education"), get_var(ds, "age")],
        )
        assert r["errors"] == []
        assert len(r["tables"][0]["rows"]) == 3
        assert r["charts"][0]["chart_type"] == "scatter_with_line"
        assert "Fitted vs Observed" in r["charts"][0]["title"]

    def test_linear_with_categorical_and_continuous_predictors(self):
        ds = make_ds(
            {
                "income": [50000, 61000, 45000, 72000, 55000, 48000, 64000, 53000],
                "gender": ["male", "female", "male", "female", "male", "female", "male", "female"],
                "education": [12, 16, 9, 18, 14, 11, 17, 13],
            }
        )
        gender = get_var(ds, "gender")
        gender.variable_type = VariableType.NOMINAL
        r = execute_analysis(
            "linear_regression",
            ds,
            get_var(ds, "income"),
            [gender, get_var(ds, "education")],
        )
        assert r["errors"] == []
        assert len(r["tables"][0]["rows"]) == 3
        assert r["charts"][0]["chart_type"] == "scatter_with_line"

    def test_linear_with_one_continuous_predictor_has_ci(self):
        ds = make_ds(
            {
                "income": [50000, 61000, 45000, 72000, 55000, 48000],
                "education": [12, 16, 9, 18, 14, 11],
            }
        )
        r = execute_analysis(
            "linear_regression",
            ds,
            get_var(ds, "income"),
            [get_var(ds, "education")],
        )
        assert r["errors"] == []
        chart = r["charts"][0]
        assert chart["chart_type"] == "scatter_with_line"
        assert "ci_lower" in chart and "ci_upper" in chart


class TestCorrelationPairwiseComplete:
    def test_pearson_uses_complete_pairs_only(self):
        from scipy import stats as sps

        x = [1.0, 2.0, None, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0]
        y = [None, 2.1, 3.2, 3.9, None, 6.1, 7.2, 8.1, 9.3, 10.2]
        ds = make_ds({"x": x, "y": y})
        r = execute_analysis(
            "pearson_correlation", ds, get_var(ds, "y"), [get_var(ds, "x")]
        )
        assert r["errors"] == []
        assert r["statistics"]["n"] == 6

        complete_x = [2.0, 4.0, 7.0, 8.0, 9.0, 10.0]
        complete_y = [2.1, 3.9, 7.2, 8.1, 9.3, 10.2]
        expected_r, _ = sps.pearsonr(complete_x, complete_y)
        assert abs(r["statistics"]["r"] - expected_r) < 1e-9

    def test_spearman_uses_complete_pairs_only(self):
        x = [1.0, 2.0, None, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0]
        y = [None, 2.1, 3.2, 3.9, None, 6.1, 7.2, 8.1, 9.3, 10.2]
        ds = make_ds({"x": x, "y": y})
        r = execute_analysis(
            "spearman_correlation", ds, get_var(ds, "y"), [get_var(ds, "x")]
        )
        assert r["errors"] == []
        assert r["statistics"]["n"] == 6

    def test_pearson_with_different_missing_counts_does_not_crash(self):
        x = [1.0, 2.0, 3.0, 4.0, None, 6.0, 7.0, 8.0]
        y = [1.1, None, 3.2, None, 5.1, None, 7.3, 8.2]
        ds = make_ds({"x": x, "y": y})
        r = execute_analysis(
            "pearson_correlation", ds, get_var(ds, "y"), [get_var(ds, "x")]
        )
        assert r["errors"] == []
        assert r["statistics"]["n"] == 4


class TestRegistry:
    def test_all_methods_registered(self):
        reg = get_registry()
        names = list(reg.keys())
        assert "independent_ttest" in names
        assert "oneway_anova" in names
        assert "pearson_correlation" in names
        assert "chi_square" in names
        assert "linear_regression" in names
        assert "frequencies" in names
        assert "descriptives" in names
        assert len(names) >= 10
