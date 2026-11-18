"""STEP 3 - irrigation features per district-year (net-area shares by source, irrigation intensity)."""
import numpy as np, pandas as pd
from config import *

d = pd.read_csv(IRR_CSV, keep_default_na=False, na_values=[""])
d["year0"] = d.year.map(start_year)
d["state_n"], d["dist_n"] = d.state_name.map(norm), d.district_name.map(norm)

net = d[(d.irrigated_area_type == "Net Irrigated Area") & d.irrigated_area.notna()]
piv = net.pivot_table(index=["state_n", "dist_n", "year0"], columns="area_sub_classification",
                      values="irrigated_area", aggfunc="sum").fillna(0)
piv["net_total"] = piv.sum(axis=1)
piv = piv[piv.net_total > 0]
for c in [c for c in piv.columns if c != "net_total"]:
    piv[f"share_{norm(c).replace(' ', '_')}"] = piv[c] / piv.net_total

gross = d[(d.irrigated_area_type == "Gross Irrigated Area") & d.irrigated_area.notna()]
piv = piv.join(gross.groupby(["state_n", "dist_n", "year0"]).irrigated_area.sum().rename("gross_total"))
piv["irr_intensity"] = piv.gross_total / piv.net_total
# gross >= net by definition; values outside ~[1, 4] are reporting errors
piv.loc[(piv.irr_intensity < 1) | (piv.irr_intensity > 4), "irr_intensity"] = np.nan

keep = [c for c in piv.columns if c.startswith("share_")] + ["net_total", "irr_intensity"]
out = piv[keep].reset_index()
out.to_csv(p("irrigation_features.csv"), index=False)
print(out.shape, "| years", out.year0.min(), "-", out.year0.max())
print(out.describe().T[["count", "mean", "min", "max"]].round(3))
