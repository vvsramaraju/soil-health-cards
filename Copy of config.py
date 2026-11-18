"""Shared settings. Upload the two datasets to DATA_DIR (default /content) before running step 1."""
import os, re

DATA_DIR = os.environ.get("DATA_DIR", "/content")
WORK = os.environ.get("WORK_DIR", "/content/work")
os.makedirs(WORK, exist_ok=True)

SHC_CSV = os.path.join(DATA_DIR, "soil_nutrient.csv")           # the big SHC file (rename yours to this)
IRR_CSV = os.path.join(DATA_DIR, "sources-of-irrigation.csv")

KEYS = ["year", "state_name", "state_code", "district_name", "district_code",
        "nutrient_name", "nutrient_level"]

MIN_SAMPLES = 30      # drop district-nutrient cells with fewer total samples
IRR_WINDOW = 3        # irrigation features = mean over this many years ending at the SHC year
MATCH_SCORE = 90      # fuzzy-match threshold (0-100) for auto-accepting district matches


def p(name):
    return os.path.join(WORK, name)


def start_year(s):
    return int(str(s)[:4])


def norm(name):
    s = str(name).lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_deficient(nutrient_name, level):
    """Rule for what counts as 'deficient / problematic'. Printed in step 2 for your review."""
    n, lv = str(nutrient_name).lower().strip(), str(level).lower().strip()
    if n in {"ph", "soil ph"}:
        return ("acid" in lv) or ("alkal" in lv)
    if "conductivity" in n or n in {"ec", "salinity"}:
        return ("saline" in lv or "sodic" in lv) and not lv.startswith("non") and "normal" not in lv
    return lv in {"deficient", "low"}
