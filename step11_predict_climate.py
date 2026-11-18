"""STEP 11 - spatially grouped CV (by state, 5 random repetitions x 5 folds), feature-set comparison.
HistGradientBoosting handles missing values natively, so every feature set is scored on the SAME rows."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from config import *

df = pd.read_csv(p("climate_analysis_table.csv"), keep_default_na=False, na_values=[""])
irr_cols = sorted([c for c in df.columns if c.startswith("share_")]) + ["irr_intensity", "net_total"]
ids = ["shc_state", "shc_dist", "year0"]
wide = df.pivot_table(index=ids, columns="nutrient_name", values="def_share").reset_index()
static = df.drop_duplicates(ids)[ids + CLIM_COLS + irr_cols]
data = wide.merge(static, on=ids)
nutrients = [c for c in wide.columns if c not in ids]
import os
folds_n, reps = 5, int(os.environ.get("REPS", 3))
states = np.array(sorted(data.shc_state.unique()))

rows = []
for nut in nutrients:
    w = data.dropna(subset=[nut]).reset_index(drop=True)
    other = [c for c in nutrients if c != nut]
    sets = {"mean_baseline": [], "other_nutrients": other,
            "other+climate": other + CLIM_COLS, "other+irrigation": other + irr_cols,
            "other+climate+irrigation": other + CLIM_COLS + irr_cols}
    y = w[nut].values
    errs = {k: [] for k in sets}
    for rep in range(reps):
        perm = np.random.default_rng(rep).permutation(states)
        fold_of = {s: i % folds_n for i, s in enumerate(perm)}
        fid = w.shc_state.map(fold_of).values
        for f in range(folds_n):
            tr, te = np.where(fid != f)[0], np.where(fid == f)[0]
            if len(te) == 0:
                continue
            for k, cols in sets.items():
                if not cols:
                    pred = np.full(len(te), y[tr].mean())
                else:
                    m = HistGradientBoostingRegressor(max_iter=100, learning_rate=0.06, random_state=0)
                    pred = m.fit(w.loc[tr, cols], y[tr]).predict(w.loc[te, cols])
                errs[k].append(np.abs(pred - y[te]).mean())
    base = np.array(errs["other_nutrients"])
    for k in sets:
        e = np.array(errs[k])
        rows.append({"nutrient": nut, "features": k, "MAE": e.mean(), "MAE_sd": e.std(),
                     "gain_vs_other_nutrients": base.mean() - e.mean(),
                     "share_of_folds_better": float((e < base).mean()), "n": len(w)})
res = pd.DataFrame(rows)
res.to_csv(p("prediction_climate_results.csv"), index=False)
print(res.pivot(index="nutrient", columns="features", values="MAE").round(4).to_string())
print("\nfraction of (rep, fold) runs in which the feature set beats other_nutrients:")
print(res.pivot(index="nutrient", columns="features", values="share_of_folds_better").round(2).to_string())
