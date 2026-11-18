"""STEP 1 - aggregate the >1 GB village-level SHC file to district x year x nutrient x level counts."""
import pandas as pd
from config import *

parts = []
for i, c in enumerate(pd.read_csv(SHC_CSV, usecols=KEYS + ["value"], chunksize=2_000_000)):
    parts.append(c.groupby(KEYS, as_index=False)["value"].sum())
    print("chunk", i, end="\r")
agg = pd.concat(parts).groupby(KEYS, as_index=False)["value"].sum()
agg.to_csv(p("shc_district_counts.csv"), index=False)

print("\nrows:", len(agg), "| years:", sorted(agg.year.unique()), "| states:", agg.state_name.nunique(),
      "| districts:", agg.district_code.nunique())
inv = agg.groupby(["nutrient_name", "nutrient_level"]).value.sum().reset_index()
inv.to_csv(p("shc_label_inventory.csv"), index=False)
print(inv.to_string(index=False))
print("\nSend me this printout (years + nutrient/level labels).")
