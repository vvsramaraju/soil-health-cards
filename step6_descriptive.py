"""STEP 6 (RQ1) - national / state / district deficiency prevalence + bar chart. Moran's I if a shapefile is given."""
import os
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import *

sh = pd.read_csv(p("deficiency_shares.csv"))           # use ALL SHC data here, not only the matched part
nat = sh.groupby("nutrient_name").apply(lambda d: d.n_def.sum() / d.n_total.sum(), include_groups=False)
nat = nat.sort_values(ascending=False)
nat.rename("deficiency_share").to_csv(p("national_deficiency_by_nutrient.csv"))
print((nat * 100).round(1).to_string())

st = sh.groupby(["state_name", "nutrient_name"]).apply(lambda d: d.n_def.sum() / d.n_total.sum(),
                                                       include_groups=False).unstack()
st.round(3).to_csv(p("state_by_nutrient_deficiency.csv"))

ax = (nat * 100).plot.bar(figsize=(9, 4), color="#b33")
ax.set_ylabel("Deficient samples (%)"); ax.set_title("National deficiency prevalence by parameter")
plt.tight_layout(); plt.savefig(p("fig_national_deficiency.png"), dpi=200)

# ---- optional spatial autocorrelation: put a district shapefile at DATA_DIR/districts.shp ----
shp = os.path.join(DATA_DIR, "districts.shp")
if os.path.exists(shp):
    import geopandas as gpd
    from libpysal.weights import Queen
    from esda.moran import Moran
    g = gpd.read_file(shp)
    print("Shapefile columns:", list(g.columns), "-> edit this block to join on your district-name column")
else:
    print("No shapefile found; skipping Moran's I (optional).")
