"""Linear regression."""

import polars as pl
import statsmodels.api as sm

from quantrix.stats.base import BaseStatMethod, StatResult
from quantrix.viz import scatter


class LinearRegression(BaseStatMethod):
    method_name = "linear_regression"
    method_family = "regression"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and at least one IV"],
            )
        yc = self._get_column(dataset, dv)
        mask = yc.is_not_null()
        preds = []
        for iv in ivs:
            pc = self._get_column(dataset, iv)
            mask = mask & pc.is_not_null()
            preds.append(pc)
        y = yc.filter(mask).to_numpy()
        n = len(y)
        if n < len(ivs) + 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=["Not enough observations"],
            )
        X_list = [pc.filter(mask).to_numpy() for pc in preds]
        X = sm.add_constant(
            pl.DataFrame({str(i): X_list[i] for i in range(len(X_list))}).to_numpy()
        )
        try:
            model = sm.OLS(y, X).fit()
        except Exception as e:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=[f"Regression failed: {e}"],
            )
        r2 = model.rsquared
        r2a = model.rsquared_adj
        fv = model.fvalue
        fp = model.f_pvalue
        dm = int(model.df_model)
        dr = int(model.df_resid)
        sig = self._format_p(fp) if fp else ""
        eff = f"R2={r2:.3f} ({r2 * 100:.1f}% of variance explained)"
        rows = [
            [
                "(Intercept)",
                round(model.params[0], 4),
                round(model.bse[0], 4) if model.bse is not None else "-",
                f"t={model.tvalues[0]:.2f}" if model.tvalues is not None else "-",
                self._format_p(model.pvalues[0]) if model.pvalues is not None else "-",
            ]
        ]
        for i, iv in enumerate(ivs):
            j = i + 1
            rows.append(
                [
                    iv.display_name,
                    round(model.params[j], 4),
                    round(model.bse[j], 4) if model.bse is not None else "-",
                    f"t={model.tvalues[j]:.2f}" if model.tvalues is not None else "-",
                    self._format_p(model.pvalues[j]) if model.pvalues is not None else "-",
                ]
            )
        names = ", ".join(iv.display_name for iv in ivs)
        # Build scatter chart with regression line
        x_raw = preds[0].filter(mask).to_numpy().tolist()
        scores = sorted(set(x_raw))
        if len(scores) > 100:
            step = len(scores) // 100
            scores = scores[::step]
        X_pred = sm.add_constant([[s] for s in scores])
        pred = model.get_prediction(X_pred)
        pred_summary = pred.summary_frame(alpha=0.05)
        line_x = scores
        line_y = [float(v) for v in pred_summary["mean"].values]
        ci_lower = [float(v) for v in pred_summary["obs_ci_lower"].values]
        ci_upper = [float(v) for v in pred_summary["obs_ci_upper"].values]
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name if ivs else "",
            statistics={
                "r_squared": r2,
                "r_squared_adj": r2a,
                "f_stat": fv if fv else 0,
                "p_value": fp if fp else 1,
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
                "f_stat": fv if fv else 0,
                "df_model": dm,
                "df_residual": dr,
                "predictor_list": names,
                "coefficient_table": "",
            },
            charts=[scatter(x_raw, y.tolist(),
                f"{dv.display_name} vs {ivs[0].display_name}",
                ivs[0].display_name, dv.display_name,
                line_x=line_x, line_y=line_y,
                ci_upper=ci_upper, ci_lower=ci_lower)],
        )
