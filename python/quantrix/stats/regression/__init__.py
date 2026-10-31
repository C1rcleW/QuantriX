"""Linear regression."""

import math
from typing import Any

import polars as pl
import statsmodels.api as sm  # type: ignore[import-untyped]

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.stats.base import BaseStatMethod, StatResult
from quantrix.viz import box_plot, scatter


def _finite_float(value: Any, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


class LinearRegression(BaseStatMethod):
    method_name = "linear_regression"
    method_family = "regression"

    def execute(
        self,
        dataset: Dataset,
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata] | None = None,
        **params: object,
    ) -> StatResult:
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and at least one IV"],
            )
        if not dv.is_continuous:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Linear regression requires a continuous dependent variable"],
            )
        df = dataset.data
        if df is None:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["No data loaded"],
            )

        missing_columns = [v.name for v in [dv, *ivs] if v.name not in df.columns]
        if missing_columns:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=[f"Variables not found: {', '.join(missing_columns)}"],
            )

        mask = df[dv.name].is_not_null()
        for iv in ivs:
            mask = mask & df[iv.name].is_not_null()
        frame = df.filter(mask)
        n = frame.height
        if n == 0:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["No complete cases for the selected variables"],
            )

        try:
            y = frame[dv.name].cast(pl.Float64).to_numpy()
        except Exception as e:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=[f"Dependent variable must be numeric: {e}"],
            )

        design_exprs: list[pl.Expr] = []
        design_names: list[str] = []
        continuous_predictors: list[bool] = []

        try:
            for i, iv in enumerate(ivs):
                if iv.variable_type == VariableType.STRING:
                    return StatResult(
                        method_name=self.method_name,
                        method_family=self.method_family,
                        n_samples=n,
                        errors=[
                            f"Predictor '{iv.display_name}' is free text and cannot be used "
                            "in linear regression"
                        ],
                    )
                numeric_ordinal = (
                    iv.variable_type == VariableType.ORDINAL
                    and frame[iv.name].dtype.is_numeric()
                )
                if iv.is_continuous or numeric_ordinal:
                    design_exprs.append(pl.col(iv.name).cast(pl.Float64).alias(f"x{i}"))
                    design_names.append(iv.display_name)
                    continuous_predictors.append(True)
                    continue

                categories = frame[iv.name].unique().sort().to_list()
                if len(categories) < 2:
                    return StatResult(
                        method_name=self.method_name,
                        method_family=self.method_family,
                        n_samples=n,
                        errors=[
                            f"Predictor '{iv.display_name}' needs at least 2 categories"
                        ],
                    )
                continuous_predictors.append(False)
                for j, category in enumerate(categories[1:]):
                    design_exprs.append(
                        (pl.col(iv.name) == category)
                        .cast(pl.Float64)
                        .alias(f"x{i}_{j}")
                    )
                    design_names.append(f"{iv.display_name} [{category}]")

            design = frame.select(design_exprs).to_numpy()
        except Exception as e:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=[f"Failed to build design matrix: {e}"],
            )

        coef_names = ["(Intercept)", *design_names]
        if n <= len(coef_names):
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=[
                    f"Not enough observations: {n} cases for {len(coef_names)} coefficients"
                ],
            )

        try:
            X = sm.add_constant(design)
            model = sm.OLS(y, X).fit()
        except Exception as e:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=[f"Regression failed: {e}"],
            )

        r2 = _finite_float(model.rsquared, 0.0)
        r2a = _finite_float(model.rsquared_adj, 0.0)
        fv = _finite_float(model.fvalue, 0.0)
        fp = _finite_float(model.f_pvalue, 1.0)
        dm = int(_finite_float(model.df_model, 0.0))
        dr = int(_finite_float(model.df_resid, 0.0))
        sig = self._format_p(fp)
        eff = f"R2={r2:.3f} ({r2 * 100:.1f}% of variance explained)"

        params_values = [float(v) for v in model.params]
        bse_values = [float(v) for v in model.bse]
        t_values = [float(v) for v in model.tvalues]
        p_values = [float(v) for v in model.pvalues]
        rows = [
            [
                name,
                round(params_values[j], 4),
                round(bse_values[j], 4),
                f"t={t_values[j]:.2f}",
                self._format_p(p_values[j]),
            ]
            for j, name in enumerate(coef_names)
        ]
        predictor_list = ", ".join(design_names)

        charts: list[dict[str, Any]] = []
        if len(ivs) == 1 and continuous_predictors[0]:
            x_values = [float(v) for v in frame[ivs[0].name].cast(pl.Float64).to_list()]
            scores = sorted(set(x_values))
            if len(scores) > 100:
                step = max(len(scores) // 100, 1)
                scores = scores[::step]
            X_pred = sm.add_constant([[score] for score in scores])
            pred_summary = model.get_prediction(X_pred).summary_frame(alpha=0.05)
            charts.append(
                scatter(
                    x_values,
                    [float(v) for v in y],
                    f"{dv.display_name} vs {ivs[0].display_name}",
                    ivs[0].display_name,
                    dv.display_name,
                    line_x=scores,
                    line_y=[float(v) for v in pred_summary["mean"]],
                    ci_upper=[float(v) for v in pred_summary["mean_ci_upper"]],
                    ci_lower=[float(v) for v in pred_summary["mean_ci_lower"]],
                )
            )
        elif len(ivs) == 1:
            y_values = [float(v) for v in y]
            groups: dict[str, list[float]] = {}
            for category, value in zip(
                frame[ivs[0].name].to_list(), y_values, strict=True
            ):
                groups.setdefault(str(category), []).append(value)
            charts.append(
                box_plot(
                    groups,
                    f"{dv.display_name} by {ivs[0].display_name}",
                    ivs[0].display_name,
                    dv.display_name,
                )
            )
        else:
            y_values = [float(v) for v in y]
            fitted_values = [float(v) for v in model.predict(X)]
            low = min([*fitted_values, *y_values])
            high = max([*fitted_values, *y_values])
            charts.append(
                scatter(
                    fitted_values,
                    y_values,
                    "Fitted vs Observed",
                    "Fitted value",
                    dv.display_name,
                    line_x=[low, high],
                    line_y=[low, high],
                )
            )

        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={
                "r_squared": r2,
                "r_squared_adj": r2a,
                "f_stat": fv,
                "p_value": fp,
                "df_model": dm,
                "df_residual": dr,
                "n": n,
            },
            effect_sizes={"r_squared": r2},
            tables=[
                {
                    "title": "Regression Coefficients",
                    "columns": ["Predictor", "B", "SE", "t", "p"],
                    "rows": rows,
                }
            ],
            sig_text=f"F({dm},{dr})={fv:.2f}, {sig}",
            effect_size_text=eff,
            misc={
                "r_squared": r2,
                "r_squared_adj": r2a,
                "r_squared_pct": r2 * 100,
                "f_stat": fv,
                "df_model": dm,
                "df_residual": dr,
                "predictor_list": predictor_list,
                "coefficient_table": "",
            },
            charts=charts,
        )
