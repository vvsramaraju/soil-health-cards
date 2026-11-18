"""STEP 4 - match SHC districts to irrigation districts (state first, then district, by name)."""
import difflib, pandas as pd
from config import *

shc = pd.read_csv(p("deficiency_shares.csv"), keep_default_na=False, na_values=[""])
irr = pd.read_csv(p("irrigation_features.csv"), keep_default_na=False, na_values=[""])
shc["state_n"], shc["shc_dist"] = shc.state_name.map(norm), shc.district_name.map(norm)


def best(name, cands):
    if len(cands) == 0:
        return None, 0
    m = max(cands, key=lambda c: difflib.SequenceMatcher(None, name, c).ratio())
    return m, round(100 * difflib.SequenceMatcher(None, name, m).ratio())


irr_states = list(irr.state_n.unique())
irr_dists = irr.groupby("state_n").dist_n.unique().to_dict()
rows = []
for s, dn in shc[["state_n", "shc_dist"]].drop_duplicates().itertuples(index=False):
    st, st_score = best(s, irr_states)
    di, di_score = best(dn, list(irr_dists.get(st, [])))
    rows.append((s, dn, st, di, st_score, di_score))
cw = pd.DataFrame(rows, columns=["shc_state", "shc_dist", "irr_state", "irr_dist", "state_score", "dist_score"])
cw["score"] = cw[["state_score", "dist_score"]].min(axis=1)
cw.sort_values("score").to_csv(p("district_crosswalk_REVIEW.csv"), index=False)
print("districts:", len(cw), "| auto-accepted (score >= %d):" % MATCH_SCORE, (cw.score >= MATCH_SCORE).sum())
print(cw[cw.score < MATCH_SCORE].sort_values("score").head(40).to_string(index=False))
print("\nOptional: edit district_crosswalk_REVIEW.csv (fix irr_state / irr_dist, set score to 100 for rows you"
      " verified), save it as district_crosswalk_REVIEWED.csv in the work folder, then run step 5.")
