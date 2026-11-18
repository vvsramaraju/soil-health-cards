"""Shared settings. Upload the two datasets to DATA_DIR (default /content) before running step 1."""
import os, re

DATA_DIR = os.environ.get("DATA_DIR", "/content")
WORK = os.environ.get("WORK_DIR", "/content/work")
os.makedirs(WORK, exist_ok=True)

def _first_existing(*names):
    for n in names:
        if os.path.exists(os.path.join(DATA_DIR, n)):
            return os.path.join(DATA_DIR, n)
    return os.path.join(DATA_DIR, names[0])


SHC_CSV = _first_existing("soil.csv", "soil_nutrient.csv")      # the big SHC file
def _find_irrigation():
    import glob
    exact = os.path.join(DATA_DIR, "sources-of-irrigation.csv")
    if os.path.exists(exact):
        return exact
    hits = [f for f in glob.glob(os.path.join(DATA_DIR, "*.csv")) if "irrigation" in os.path.basename(f).lower()]
    return sorted(hits)[0] if hits else exact


IRR_CSV = _find_irrigation()

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


def _find_climate():
    import glob
    hits = [f for f in glob.glob(os.path.join(DATA_DIR, "*.csv")) if "climate" in os.path.basename(f).lower()]
    return sorted(hits)[0] if hits else os.path.join(DATA_DIR, "district-wise-climate-vulnerability-indicators.csv")


CLIM_CSV = _find_climate()
# pre-specified climate/context covariates (all others in that file are >70% empty): primary = climate_vul_in
CLIM_COLS = ["climate_vul_in", "area_rainfed_agri", "mar_small_land", "yield_variability", "livestock"]


def _find_health():
    import glob
    hits = [f for f in glob.glob(os.path.join(DATA_DIR, "*.csv")) if "health-indicators" in os.path.basename(f).lower()
            or "health_indicators" in os.path.basename(f).lower()]
    return sorted(hits)[0] if hits else os.path.join(DATA_DIR, "major-health-indicators-subdistrict-level.csv")


HEALTH_CSV = _find_health()
HEALTH_YEAR = "2019"   # the only full year (2017-18 have ~20 rows/month; 2020 is partial)
