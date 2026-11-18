"""STEP 5 - merge deficiency shares with window-averaged irrigation features."""
import os, pandas as pd
from config import *

shc = pd.read_csv(p("deficiency_shares.csv"), keep_default_na=False, na_values=[""])
irr = pd.read_csv(p("irrigation_features.csv"), keep_default_na=False, na_values=[""])
rev = p("district_crosswalk_REVIEWED.csv")
cw = pd.read_csv(rev if os.path.exists(rev) else p("district_crosswalk_REVIEW.csv"), keep_default_na=False, na_values=[""])
print("using crosswalk:", "REVIEWED" if os.path.exists(rev) else "auto (unreviewed)")
cw = cw[cw.score >= MATCH_SCORE]

shc["shc_state"], shc["shc_dist"] = shc.state_name.map(norm), shc.district_name.map(norm)
sh = shc.merge(cw[["shc_state", "shc_dist", "irr_state", "irr_dist"]], on=["shc_state", "shc_dist"])

# window average: value from year t contributes to target years t .. t+W-1
feat_cols = [c for c in irr.columns if c not in ("state_n", "dist_n", "year0")]
shifted = []
for k in range(IRR_WINDOW):
    t = irr.copy(); t["year0"] = t.year0 + k; shifted.append(t)
win = pd.concat(shifted).groupby(["state_n", "dist_n", "year0"], as_index=False)[feat_cols].mean()
win = win.rename(columns={"state_n": "irr_state", "dist_n": "irr_dist"})

df = sh.merge(win, on=["irr_state", "irr_dist", "year0"], how="inner")
df.to_csv(p("analysis_table.csv"), index=False)
print("SHC cells:", len(shc), "-> matched with irrigation:", len(df),
      f"({100*len(df)/len(shc):.0f}% coverage)")
print("districts:", df[["irr_state", "irr_dist"]].drop_duplicates().shape[0], "| years:", sorted(df.year0.unique()))
