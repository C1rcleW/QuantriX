"""Correlation: Pearson, Spearman, Chi-square."""

from scipy import stats as sps

from quantrix.stats.base import BaseStatMethod, StatResult
from quantrix.viz import bar, scatter


class PearsonCorrelation(BaseStatMethod):
    method_name = "pearson_correlation"
    method_family = "correlation"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Two variables required"],
            )
        xc = self._get_valid(dataset, dv)
        yc = self._get_valid(dataset, ivs[0])
        mask = xc.is_not_null() & yc.is_not_null()
        x = xc.filter(mask).to_numpy()
        y = yc.filter(mask).to_numpy()
        n = len(x)
        if n < 3:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=["Not enough valid pairs"],
            )
        r, p = sps.pearsonr(x, y)
        r2 = r**2
        ra = abs(r)
        strength = (
            "negligible"
            if ra < 0.1
            else ("weak" if ra < 0.3 else ("moderate" if ra < 0.5 else "strong"))
        )
        direction = "positive" if r >= 0 else "negative"
        sig = self._format_p(p)
        x_list = x.tolist()
        y_list = y.tolist()
        x_mean = float(x.mean()); y_mean = float(y.mean())
        sx = float(x.std(ddof=1)); sy = float(y.std(ddof=1))
        slope = r * sy / sx if sx > 0 else 0
        intercept = y_mean - slope * x_mean
        x_range = [float(x.min()), float(x.max())]
        line_y = [intercept + slope * xr for xr in x_range]
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={"r": r, "r_squared": r2, "p_value": p, "n": n, "df": n - 2},
            effect_sizes={"r": r, "r_squared": r2},
            sig_text=f"r({n - 2})={r:.3f}, {sig}",
            effect_size_text=f"{strength} {direction} correlation",
            misc={"r": r, "df": n - 2, "n": n, "strength": strength, "direction": direction},
            charts=[scatter(x_list, y_list,
                f"{dv.display_name} vs {ivs[0].display_name}",
                ivs[0].display_name, dv.display_name,
                line_x=x_range, line_y=line_y)],
        )


class SpearmanCorrelation(BaseStatMethod):
    method_name = "spearman_correlation"
    method_family = "correlation"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Two variables required"],
            )
        xc = self._get_valid(dataset, dv)
        yc = self._get_valid(dataset, ivs[0])
        mask = xc.is_not_null() & yc.is_not_null()
        x = xc.filter(mask).to_numpy()
        y = yc.filter(mask).to_numpy()
        n = len(x)
        if n < 3:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=n,
                errors=["Not enough valid pairs"],
            )
        rho, p = sps.spearmanr(x, y)
        sig = self._format_p(p)
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={"rho": rho, "p_value": p, "n": n},
            effect_sizes={"rho": rho},
            sig_text=f"rho={rho:.3f}, {sig}",
            effect_size_text="",
            misc={"rho": rho, "n": n},
            charts=[scatter(x.tolist(), y.tolist(),
                f"{dv.display_name} vs {ivs[0].display_name}",
                ivs[0].display_name, dv.display_name)],
        )


class ChiSquare(BaseStatMethod):
    method_name = "chi_square"
    method_family = "correlation"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Two variables required"],
            )
        if dv.is_continuous or ivs[0].is_continuous:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Chi-square requires categorical variables"],
            )
        c1 = self._get_column(dataset, dv)
        c2 = self._get_column(dataset, ivs[0])
        mask = c1.is_not_null() & c2.is_not_null()
        fdf = dataset.data.filter(mask) if dataset.data is not None else None
        if fdf is None or fdf.height < 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Not enough valid data"],
            )
        n = fdf.height
        pivot = (
            fdf.group_by([ivs[0].name, dv.name])
            .len()
            .pivot(values="len", index=ivs[0].name, on=dv.name)
            .fill_null(0)
        )
        observed = pivot.select(pivot.columns[1:]).to_numpy()
        chi2, p, dof, expected = sps.chi2_contingency(observed)
        cramer = (chi2 / (n * (min(observed.shape) - 1))) ** 0.5 if min(observed.shape) > 1 else 0
        sig = self._format_p(p)
        rows = [[str(r[0])] + [str(v) for v in r[1:]] for r in pivot.iter_rows()]
        cats = pivot.columns[1:]
        series = [{"name": str(row[0]), "data": [int(v) if str(v).isdigit() else 0 for v in row[1:]]} for row in rows]
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={"chi_squared": chi2, "p_value": p, "df": dof, "n": n},
            effect_sizes={"cramers_v": cramer},
            tables=[
                {
                    "title": f"Crosstab: {dv.display_name} x {ivs[0].display_name}",
                    "columns": [ivs[0].name] + [str(c) for c in pivot.columns[1:]],
                    "rows": rows,
                }
            ],
            sig_text=f"chisq({dof})={chi2:.2f}, {sig}",
            effect_size_text=f"Cramer V={cramer:.3f}",
            misc={"n": n},
            charts=[bar([str(c) for c in cats], [int(sum(s["data"])) if isinstance(s["data"], list) else 0 for s in series],
                f"{dv.display_name} x {ivs[0].display_name}", ivs[0].display_name, "Count")],
        )
