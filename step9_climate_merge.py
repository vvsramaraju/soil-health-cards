"""STEP 9 - add district climate-vulnerability covariates (static, 2021 snapshot) to the SHC deficiency table.
Merges onto ALL SHC districts (not only those with irrigation data); irrigation features are attached where available."""
import os, difflib, pandas as pd
from config import *

kw = dict(keep_default_na=False, na_values=[""])
shc = pd.read_csv(p("deficiency_shares.csv"), **kw)
clim = pd.read_csv(CLIM_CSV, **kw)
shc["shc_state"], shc["shc_dist"] = shc.state_name.map(norm), shc.district_name.map(norm)
clim["c_state"], clim["c_dist"] = clim.state_name.map(norm), clim.district_name.map(norm)


def best(name, cands):
    if len(cands) == 0:
        return None, 0
    m = max(cands, key=lambda c: difflib.SequenceMatcher(None, name, c).ratio())
    return m, round(100 * difflib.SequenceMatcher(None, name, m).ratio())


cstates = list(clim.c_state.unique())
cd = clim.groupby("c_state").c_dist.unique().to_dict()
rows = []
for s, dn in shc[["shc_state", "shc_dist"]].drop_duplicates().itertuples(index=False):
    st, ss = best(s, cstates)
    di, ds = best(dn, list(cd.get(st, [])))
    rows.append((s, dn, st, di, min(ss, ds)))
cw = pd.DataFrame(rows, columns=["shc_state", "shc_dist", "c_state", "c_dist", "score"])
cw.sort_values("score").to_csv(p("climate_crosswalk_REVIEW.csv"), index=False)
rev = p("climate_crosswalk_REVIEWED.csv")
if os.path.exists(rev):
    cw = pd.read_csv(rev, **kw); print("using REVIEWED climate crosswalk")
cw_ok = cw[cw.score >= MATCH_SCORE]
print("SHC districts:", len(cw), "| matched to climate data:", len(cw_ok))
print(cw[cw.score < MATCH_SCORE].sort_values("score").head(30).to_string(index=False))

feat = clim[["c_state", "c_dist"] + CLIM_COLS].merge(cw_ok, on=["c_state", "c_dist"])
feat = feat.drop(columns=["c_state", "c_dist", "score"])
df = shc.merge(feat, on=["shc_state", "shc_dist"], how="inner")
# standardise climate covariates across districts (so effects are "per +1 SD")
dist = df.drop_duplicates(["shc_state", "shc_dist"])
for c in CLIM_COLS:
    df[f"z_{c}"] = (df[c] - dist[c].mean()) / dist[c].std()

# attach irrigation features (where available) from the step-5 table
at = p("analysis_table.csv")
if os.path.exists(at):
    a = pd.read_csv(at, **kw)
    irr_cols = [c for c in a.columns if c.startswith("share_")] + ["irr_intensity", "net_total"]
    df = df.merge(a[["year", "shc_state", "shc_dist", "nutrient_name"] + irr_cols],
                  on=["year", "shc_state", "shc_dist", "nutrient_name"], how="left")
df.to_csv(p("climate_analysis_table.csv"), index=False)
print("cells:", len(df), "| districts:", df[["shc_state", "shc_dist"]].drop_duplicates().shape[0],
      "| with climate index:", df.climate_vul_in.notna().sum(), "| with irrigation:", df.net_total.notna().sum()
      if "net_total" in df else "")
print(dist[CLIM_COLS].notna().mean().round(2).to_string())
