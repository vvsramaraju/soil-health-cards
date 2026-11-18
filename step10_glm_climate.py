"""STEP 10 - binomial GLM: deficiency share ~ climate vulnerability (+ irrigation) with / without state effects.
Model A: national gradient (no state effects). Model B: within-state (state effects). Model C: B + irrigation shares."""
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from config import *

df = pd.read_csv(p("climate_analysis_table.csv"), keep_default_na=False, na_values=[""])
share_cols = sorted([c for c in df.columns if c.startswith("share_")])
ref = "share_tubewell" if "share_tubewell" in share_cols else share_cols[-1]
irr_terms = [c for c in share_cols if c != ref] + ["irr_intensity"]
primary = "z_climate_vul_in"
rows = []
for nut, d0 in df.groupby("nutrient_name"):
    for model, extra, need, use_state in [("A_no_state_effects", [], [primary], False),
                                          ("B_state_effects", [], [primary], True),
                                          ("C_state+irrigation", irr_terms, [primary] + irr_terms, True)]:
        d = d0.dropna(subset=need + ["def_share"]).copy()
        d["n_ok"] = d.n_total - d.n_def
        if len(d) < 200 or d.shc_state.nunique() < 5:
            continue
        f = "n_def + n_ok ~ " + " + ".join([primary] + extra) + (" + C(shc_state)" if use_state else "")
        try:
            r = smf.glm(f, data=d, family=sm.families.Binomial()).fit(
                cov_type="cluster", cov_kwds={"groups": pd.factorize(d.shc_state)[0]})
        except Exception as e:
            print("skip", nut, model, e); continue
        b, se = r.params[primary], r.bse[primary]
        rows.append({"nutrient": nut, "model": model, "odds_ratio_per_SD": np.exp(b),
                     "ci_low": np.exp(b - 1.96 * se), "ci_high": np.exp(b + 1.96 * se), "p": r.pvalues[primary],
                     "n_cells": len(d), "n_states": d.shc_state.nunique()})
res = pd.DataFrame(rows)
# Benjamini-Hochberg within each model
for m, g in res.groupby("model"):
    o = g.p.sort_values().index; k = len(o)
    adj = (g.p.loc[o] * k / np.arange(1, k + 1))[::-1].cummin()[::-1].clip(upper=1)
    res.loc[o, "q_BH"] = adj.values
res.to_csv(p("glm_climate_results.csv"), index=False)
print(res.round(4).to_string(index=False))
