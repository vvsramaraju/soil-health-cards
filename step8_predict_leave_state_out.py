"""STEP 8 (RQ3) - leave-state-out prediction of a nutrient's deficiency share; with / without irrigation features."""
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from config import *

df = pd.read_csv(p("analysis_table.csv"))
irr_cols = sorted([c for c in df.columns if c.startswith("share_")]) + ["irr_intensity", "net_total"]
ids = ["irr_state", "irr_dist", "year0"]
wide = df.pivot_table(index=ids, columns="nutrient_name", values="def_share").reset_index()
irr = df.drop_duplicates(ids)[ids + irr_cols]
data = wide.merge(irr, on=ids)
nutrients = [c for c in wide.columns if c not in ids]

rows = []
for nut in nutrients:
    w = data.dropna(subset=[nut]).reset_index(drop=True)
    if len(w) < 200 or w.irr_state.nunique() < 5:
        continue
    other = [c for c in nutrients if c != nut]
    y = w[nut].values
    sets = {"mean_baseline": [], "irrigation_only": irr_cols,
            "other_nutrients": other, "other_nutrients+irrigation": other + irr_cols}
    for name, cols in sets.items():
        maes = []
        for tr, te in GroupKFold(n_splits=5).split(w, y, groups=w.irr_state):
            if not cols:
                pred = np.full(len(te), y[tr].mean())
            else:
                Xtr, Xte = w.loc[tr, cols], w.loc[te, cols]
                med = Xtr.median()                       # imputation fitted on TRAIN only
                m = GradientBoostingRegressor(random_state=0).fit(Xtr.fillna(med), y[tr])
                pred = m.predict(Xte.fillna(med))
            maes.append(np.abs(pred - y[te]).mean())
        rows.append({"nutrient": nut, "features": name, "MAE_mean": np.mean(maes), "MAE_std": np.std(maes),
                     "n": len(w)})
res = pd.DataFrame(rows)
res.to_csv(p("prediction_results.csv"), index=False)
print(res.pivot(index="nutrient", columns="features", values="MAE_mean").round(4).to_string())
