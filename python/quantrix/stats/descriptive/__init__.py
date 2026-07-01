"""Descriptive statistics."""
from quantrix.stats.base import BaseStatMethod, StatResult

class Frequencies(BaseStatMethod):
    method_name = "frequencies"
    method_family = "descriptive"
    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None: return StatResult(method_name=self.method_name, method_family=self.method_family, n_samples=0, errors=["No variable"])
        valid = self._get_valid(dataset, dv)
        n_total = len(self._get_column(dataset, dv)); n_valid = len(valid)
        freq = valid.value_counts().sort("count", descending=True); n_cat = freq.height
        mode_cat = str(freq[0,0]) if n_cat > 0 else "-"; mode_count = freq[0,1] if n_cat > 0 else 0
        rows = [[str(r[0]), r[1], round(r[1]/n_valid*100,1) if n_valid else 0] for r in freq.iter_rows()]
        cat_sum = ", ".join(f"{r[0]} (n={r[1]}, {r[2]}%)" for r in rows[:8])
        return StatResult(method_name=self.method_name, method_family=self.method_family, n_samples=n_total, dv_label=dv.display_name, statistics={"n_total":n_total,"n_valid":n_valid,"n_missing":n_total-n_valid,"n_categories":n_cat}, tables=[{"title":f"Frequency: {dv.display_name}", "columns":["Category","n","%"], "rows":rows}], sig_text=f"N={n_valid}, {n_cat} categories", effect_size_text=f"Mode: {mode_cat} ({mode_count})", misc={"category_summary":cat_sum,"mode_category":mode_cat,"mode_count":mode_count,"n_categories":n_cat,"n":n_total})

class Descriptives(BaseStatMethod):
    method_name = "descriptives"
    method_family = "descriptive"
    def execute(self, dataset, dv, ivs=None, **params):
        if dv is None: return StatResult(method_name=self.method_name, method_family=self.method_family, n_samples=0, errors=["No variable"])
        col = self._get_column(dataset, dv); valid = self._get_valid(dataset, dv); n = len(valid)
        if n == 0: return StatResult(method_name=self.method_name, method_family=self.method_family, n_samples=len(col), errors=["No valid data"])
        m = valid.mean(); s = valid.std(); mn = valid.min(); mx = valid.max(); md = valid.median()
        q1 = valid.quantile(0.25); q3 = valid.quantile(0.75)
        sk = ((valid-m)**3).mean()/(s**3) if s and s>0 else 0.0
        sk_txt = f"Skewed (skewness={sk:.2f})" if abs(sk) > 1 else ""
        rows = [["N",n],["Mean",round(m,2)],["SD",round(s,2)],["Min",round(mn,2)],["Q1",round(q1,2)],["Median",round(md,2)],["Q3",round(q3,2)],["Max",round(mx,2)]]
        return StatResult(method_name=self.method_name, method_family=self.method_family, n_samples=len(col), dv_label=dv.display_name, statistics={"n":len(col),"n_valid":n,"mean":m,"std_dev":s,"min":mn,"max":mx,"median":md,"q1":q1,"q3":q3,"skewness":sk,"missing_count":len(col)-n}, tables=[{"title":f"Descriptives: {dv.display_name}","columns":["Stat","Value"],"rows":rows}], sig_text=f"N={n}", misc={"n":len(col),"n_valid":n,"missing_count":len(col)-n,"mean":m,"std_dev":s,"min_val":mn,"max_val":mx,"skewness_text":sk_txt,"missing_pct":round((len(col)-n)/len(col)*100,1) if len(col)>0 else 0})
