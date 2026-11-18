"""STEP 12 (exploratory) - district health proxies (HMIS 2019) vs soil deficiency, within-state.
Uses sector == 'Total' ONLY (Rural/Urban/Public/Private are overlapping cuts -> summing would double count).
Health indicators (pre-specified): anaemia_pw, lbw, sam_per_1000."""
import difflib, numpy as np, pandas as pd
from scipy.stats import spearmanr
from config import *

cols = ["date", "state_name", "district_name", "sector", "pw_hb7_10_9", "pw_hb_lt7", "pw_anc_reg", "nb_lt2_5kg",
        "nb_weighed_birth", "child_sam", "live_birth_female", "live_birth_male"]
h = pd.read_csv(HEALTH_CSV, usecols=cols, keep_default_na=False, na_values=[""])
h = h[(h.sector == "Total") & (h.date.str[:4] == HEALTH_YEAR)]
g = h.groupby(["state_name", "district_name"], as_index=False).sum(numeric_only=True)
g["births"] = g.live_birth_female + g.live_birth_male
ok = lambda s, k=500: s.where(s >= k)                      # drop districts with tiny denominators
g["anaemia_pw"] = 100 * (g.pw_hb7_10_9 + g.pw_hb_lt7) / ok(g.pw_anc_reg)
g["lbw"] = 100 * g.nb_lt2_5kg / ok(g.nb_weighed_birth)
g["sam_per_1000"] = 1000 * g.child_sam / ok(g.births)
HV = ["anaemia_pw", "lbw", "sam_per_1000"]
for v in HV:                                               # winsorise reporting artefacts at 1st/99th percentile
    lo, hi = g[v].quantile([0.01, 0.99]); g[v] = g[v].clip(lo, hi)
g["h_state"], g["h_dist"] = g.state_name.map(norm), g.district_name.map(norm)
g.to_csv(p("health_district_features.csv"), index=False)

s = pd.read_csv(p("deficiency_shares.csv"), keep_default_na=False, na_values=[""])
s["shc_state"], s["shc_dist"] = s.state_name.map(norm), s.district_name.map(norm)
hs = list(g.h_state.unique()); hd = g.groupby("h_state").h_dist.unique().to_dict()


def best(n, c):
    m = max(c, key=lambda x: difflib.SequenceMatcher(None, n, x).ratio()); return m, 100 * difflib.SequenceMatcher(None, n, m).ratio()


rows = []
for st, dn in s[["shc_state", "shc_dist"]].drop_duplicates().itertuples(index=False):
    bs, a = best(st, hs); bd, b = best(dn, list(hd[bs]))
    rows.append((st, dn, bs, bd, round(min(a, b))))
cw = pd.DataFrame(rows, columns=["shc_state", "shc_dist", "h_state", "h_dist", "score"])
cw.sort_values("score").to_csv(p("health_crosswalk_REVIEW.csv"), index=False)
print("SHC districts:", len(cw), "| matched:", (cw.score >= MATCH_SCORE).sum())

sh = s.groupby(["shc_state", "shc_dist", "nutrient_name"]).apply(
    lambda d: d.n_def.sum() / d.n_total.sum(), include_groups=False).unstack().reset_index()
m = sh.merge(cw[cw.score >= MATCH_SCORE], on=["shc_state", "shc_dist"]).merge(
    g[["h_state", "h_dist"] + HV], on=["h_state", "h_dist"])
m.to_csv(p("health_soil_district_table.csv"), index=False)
print("merged districts:", len(m))

out = []
for n in [c for c in sh.columns if c not in ("shc_state", "shc_dist")]:
    for v in HV:
        d = m[["shc_state", n, v]].dropna()
        if len(d) < 100:
            continue
        r0, _ = spearmanr(d[n], d[v])
        a = d[n] - d.groupby("shc_state")[n].transform("mean"); b = d[v] - d.groupby("shc_state")[v].transform("mean")
        r1, p1 = spearmanr(a, b); out.append((n, v, len(d), r0, r1, p1))
res = pd.DataFrame(out, columns=["soil_nutrient", "health_indicator", "districts", "rho_raw", "rho_within_state", "p_within"])
k = len(res); o = res.p_within.sort_values().index
res.loc[o, "q_BH"] = (res.p_within[o] * k / np.arange(1, k + 1))[::-1].cummin()[::-1].clip(upper=1).values
res.round(4).to_csv(p("health_soil_association.csv"), index=False)
print(res.round(3).to_string(index=False))
