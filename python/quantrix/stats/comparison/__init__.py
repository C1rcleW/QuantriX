"""Group comparison: t-test, ANOVA, non-parametric."""

from scipy import stats as sps

from quantrix.stats.base import BaseStatMethod, StatResult
from quantrix.viz import box_plot, grouped_bar


class IndependentTTest(BaseStatMethod):
    method_name = "independent_ttest"
    method_family = "comparison"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and IV"],
            )
        col = self._get_column(dataset, dv)
        group_col = self._get_column(dataset, ivs[0])
        mask = col.is_not_null() & group_col.is_not_null()
        groups = group_col.filter(mask).unique().sort().to_list()
        if len(groups) != 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need exactly 2 groups"],
            )
        g1 = col.filter(mask & (group_col == groups[0])).to_numpy()
        g2 = col.filter(mask & (group_col == groups[1])).to_numpy()
        t, p = sps.ttest_ind(g1, g2)
        n1, n2 = len(g1), len(g2)
        m1, m2 = g1.mean(), g2.mean()
        s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
        d = self._cohens_d(m1, m2, s1, s2, n1, n2)
        sig = self._format_p(p)
        df_val = n1 + n2 - 2
        g1_name, g2_name = str(groups[0]), str(groups[1])
        bp_data = {g1_name: g1.tolist(), g2_name: g2.tolist()}
        gb_data = [
            {"name": "Mean", "data": [round(float(m1), 2), round(float(m2), 2)]},
            {"name": "SD", "data": [round(float(s1), 2), round(float(s2), 2)]},
        ]
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n1 + n2,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            group_labels=[g1_name, g2_name],
            statistics={
                "t_stat": t,
                "p_value": p,
                "df": df_val,
                "n1": n1,
                "n2": n2,
                "mean1": m1,
                "mean2": m2,
                "sd1": s1,
                "sd2": s2,
            },
            effect_sizes={"cohens_d": d},
            tables=[
                {
                    "title": f"t-test: {dv.display_name}",
                    "columns": ["Group", "N", "Mean", "SD"],
                    "rows": [
                        [str(groups[0]), n1, round(m1, 2), round(s1, 2)],
                        [str(groups[1]), n2, round(m2, 2), round(s2, 2)],
                    ],
                }
            ],
            sig_text=f"t({df_val})={t:.3f}, {sig}",
            effect_size_text=f"Cohen's d={d:.3f}",
            misc={"means": [m1, m2], "sds": [s1, s2], "ns": [n1, n2]},
            charts=[
                box_plot(bp_data, f"{dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name),
                grouped_bar([g1_name, g2_name], gb_data, f"Mean {dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name),
            ],
        )


class OneWayANOVA(BaseStatMethod):
    method_name = "oneway_anova"
    method_family = "comparison"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and IV"],
            )
        col = self._get_column(dataset, dv)
        gc = self._get_column(dataset, ivs[0])
        mask = col.is_not_null() & gc.is_not_null()
        groups = gc.filter(mask).unique().sort().to_list()
        group_data = [col.filter(mask & (gc == g)).to_numpy() for g in groups]
        if len(group_data) < 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need >=2 groups"],
            )
        f_stat, p = sps.f_oneway(*group_data)
        n_total = sum(len(g) for g in group_data)
        sig = self._format_p(p)
        rows = [
            [
                str(groups[i]),
                len(group_data[i]),
                round(group_data[i].mean(), 2),
                round(group_data[i].std(ddof=1), 2),
            ]
            for i in range(len(groups))
        ]
        bp_data = {str(groups[i]): group_data[i].tolist() for i in range(len(groups))}
        gb_cats = [str(g) for g in groups]
        gb_data = [
            {"name": "Mean", "data": [round(float(gd.mean()), 2) for gd in group_data]},
            {"name": "SD", "data": [round(float(gd.std(ddof=1)), 2) for gd in group_data]},
        ]
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=n_total,
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={
                "f_stat": f_stat,
                "p_value": p,
                "df_between": len(groups) - 1,
                "df_within": n_total - len(groups),
                "n_groups": len(groups),
            },
            tables=[
                {
                    "title": f"ANOVA: {dv.display_name}",
                    "columns": ["Group", "N", "Mean", "SD"],
                    "rows": rows,
                }
            ],
            sig_text=f"F({len(groups) - 1},{n_total - len(groups)})={f_stat:.3f}, {sig}",
            effect_size_text="",
            misc={"n_groups": len(groups), "group_table": ""},
            charts=[
                box_plot(bp_data, f"{dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name),
                grouped_bar(gb_cats, gb_data, f"Mean {dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name),
            ],
        )


class MannWhitney(BaseStatMethod):
    method_name = "mann_whitney"
    method_family = "comparison"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and IV"],
            )
        col = self._get_column(dataset, dv)
        gc = self._get_column(dataset, ivs[0])
        mask = col.is_not_null() & gc.is_not_null()
        groups = gc.filter(mask).unique().sort().to_list()
        if len(groups) != 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need exactly 2 groups"],
            )
        g1 = col.filter(mask & (gc == groups[0])).to_numpy()
        g2 = col.filter(mask & (gc == groups[1])).to_numpy()
        u, p = sps.mannwhitneyu(g1, g2, alternative="two-sided")
        g1_name, g2_name = str(groups[0]), str(groups[1])
        bp_data = {g1_name: g1.tolist(), g2_name: g2.tolist()}
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=len(g1) + len(g2),
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            group_labels=[g1_name, g2_name],
            statistics={"u_stat": u, "p_value": p, "n1": len(g1), "n2": len(g2)},
            sig_text=f"U={u:.1f}, {self._format_p(p)}",
            effect_size_text="",
            charts=[box_plot(bp_data, f"{dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name)],
        )


class KruskalWallis(BaseStatMethod):
    method_name = "kruskal_wallis"
    method_family = "comparison"

    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None or not ivs:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need DV and IV"],
            )
        col = self._get_column(dataset, dv)
        gc = self._get_column(dataset, ivs[0])
        mask = col.is_not_null() & gc.is_not_null()
        groups = gc.filter(mask).unique().sort().to_list()
        group_data = [col.filter(mask & (gc == g)).to_numpy() for g in groups]
        if len(group_data) < 2:
            return StatResult(
                method_name=self.method_name,
                method_family=self.method_family,
                n_samples=0,
                errors=["Need >=2 groups"],
            )
        h, p = sps.kruskal(*group_data)
        bp_data = {str(groups[i]): group_data[i].tolist() for i in range(len(groups))}
        return StatResult(
            method_name=self.method_name,
            method_family=self.method_family,
            n_samples=sum(len(g) for g in group_data),
            dv_label=dv.display_name,
            iv_label=ivs[0].display_name,
            statistics={"h_stat": h, "p_value": p, "n_groups": len(groups)},
            sig_text=f"H({len(groups) - 1})={h:.3f}, {self._format_p(p)}",
            effect_size_text="",
            misc={"n_groups": len(groups)},
            charts=[box_plot(bp_data, f"{dv.display_name} by {ivs[0].display_name}", ivs[0].display_name, dv.display_name)],
        )
