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
