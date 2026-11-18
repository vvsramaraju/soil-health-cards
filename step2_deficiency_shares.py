"""STEP 2 - deficiency share per district x year x nutrient."""
import pandas as pd
from config import *

agg = pd.read_csv(p("shc_district_counts.csv"))
agg["is_def"] = [is_deficient(n, l) for n, l in zip(agg.nutrient_name, agg.nutrient_level)]

# show the rule actually applied -> CHECK THIS TABLE
rule = agg.groupby(["nutrient_name", "nutrient_level"]).is_def.first().reset_index()
print(rule.to_string(index=False))
rule.to_csv(p("deficiency_rule_applied.csv"), index=False)

agg["def_count"] = agg.value.where(agg.is_def, 0)
keys = ["year", "state_name", "district_name", "district_code", "nutrient_name"]
out = agg.groupby(keys, as_index=False).agg(n_def=("def_count", "sum"), n_total=("value", "sum"))
out = out[out.n_total >= MIN_SAMPLES].copy()
out["def_share"] = out.n_def / out.n_total
out["year0"] = out.year.map(start_year)
out.to_csv(p("deficiency_shares.csv"), index=False)
print("\ncells kept:", len(out)); print(out.groupby("nutrient_name").def_share.describe().round(3))
