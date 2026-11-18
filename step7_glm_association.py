"""STEP 7 (RQ2) - binomial GLM: deficiency share ~ irrigation source shares + intensity + state effects."""
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from config import *

df = pd.read_csv(p("analysis_table.csv"))
share_cols = sorted([c for c in df.columns if c.startswith("share_")])
drop = "share_tubewell" if "share_tubewell" in share_cols else share_cols[-1]   # reference category (shares sum to 1)
xs = [c for c in share_cols if c != drop] + ["irr_intensity"]
rows = []
for nut, d in df.groupby("nutrient_name"):
    d = d.dropna(subset=xs + ["def_share"]).copy()
    d["n_ok"] = d.n_total - d.n_def
    if len(d) < 200 or d.irr_state.nunique() < 5:
        continue
    f = "n_def + n_ok ~ " + " + ".join(xs) + " + C(irr_state)"
    try:
        r = smf.glm(f, data=d, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d.irr_state)[0]})
    except Exception as e:
        print("skip", nut, e); continue
    for x in xs:
        rows.append({"nutrient": nut, "term": x, "coef": r.params[x], "se": r.bse[x], "p": r.pvalues[x],
                     "odds_ratio_per_+10pp": float(np.exp(r.params[x] * 0.1)) if x.startswith("share_") else np.nan,
                     "n": len(d)})
res = pd.DataFrame(rows)
res.to_csv(p("glm_results.csv"), index=False)
print("reference source share dropped:", drop)
print(res.round(4).to_string(index=False))
