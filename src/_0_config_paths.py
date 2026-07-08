# src/_0_config_paths.py
# ============================================================
# PATH CONFIGURATION
#
# All paths are derived automatically from DATA_RAW and STUDY_AREA.
# Do NOT edit paths manually - change STUDY_AREA in _00_config.py instead.
#
# Also contains:
#   - SWORD continent auto-detection from PFAF_IDS
#   - SAGA GIS auto-detection for floodplain computation
# ============================================================

import os
import glob
from _00_config import STUDY_AREA, PFAF_IDS, PFAF_LEVEL_DIGITS, REACH_TYPES_TO_KEEP

# ============================================================
# Base directories --> edit these to match your local setup
# ============================================================
DATA_RAW       = r"D:\0_InnoLab\0_data"
DATA_PROCESSED = r"C:\Users\Duck\Documents\Studium\EAGLE\04_semester\0_InnoLab\RiverEggCode\data\processed"
DATA_OUTPUT    = r"C:\Users\Duck\Documents\Studium\EAGLE\04_semester\0_InnoLab\RiverEggCode\data\outputs"


# ============================================================
# SWORD Continental File Selection
# Continent is auto-derived from the first digit of PFAF_IDS.
# The first digit of the Pfafstetter code encodes the continent.
# ============================================================

PFAF_CONTINENT_MAP = {
    1: "af",   # Africa
    2: "eu",   # Europe
    3: "as",   # Siberia / North Asia (Lena, Ob, Yenisei)
    4: "as",   # Asia (Naryn, Mekong, Indus, ...)
    5: "oc",   # Australia / Oceania
    6: "sa",   # South America
    7: "na",   # North America
    8: "na",   # North America (Arctic / Canada)
    9: "na",   # Arctic
}

# Paths to all available continental SWORD files
SWORD_FILES = {
    "as": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "as_sword_reaches_v17b.gpkg"),
    "af": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "af_sword_reaches_v17b.gpkg"),
    "eu": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "eu_sword_reaches_v17b.gpkg"),
    "na": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "na_sword_reaches_v17b.gpkg"),
    "sa": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "sa_sword_reaches_v17b.gpkg"),
    "oc": os.path.join(DATA_RAW, "SWOT_river_database_SWORD", "oc_sword_reaches_v17b.gpkg"),
}

# Auto-detect continent from PFAF_IDS
# All PFAF_IDs in one study area must belong to the same continent.
# Cross-continent rivers (e.g. Nile) are not yet supported.
_continent_codes = set(PFAF_CONTINENT_MAP.get(int(str(p)[0])) for p in PFAF_IDS)
if len(_continent_codes) > 1:
    raise ValueError(
        f"PFAF_IDs span multiple continents: {_continent_codes}. "
        f"Multi-continent rivers are not yet supported - "
        f"split into separate study areas."
    )

CONTINENT = _continent_codes.pop()
IN_SWORD  = SWORD_FILES[CONTINENT]

# HydroBASINS Level 5 - used for AOI polygon definition
IN_BASIN_5 = os.path.join(
    DATA_RAW, "BasinATLAS_HydroSHEDS",
    "BasinATLAS_v10_lev05.gpkg"
)


# ============================================================
# SAGA GIS Configuration
# SAGA is used for floodplain indicator computation (MRVBF, VD, HD).
# Installed as part of QGIS or standalone on Windows.
# Automatically searches common installation paths.
# NOTE: modifying os.environ["PATH"] affects the entire Python session.
# ============================================================

def _find_saga_cmd():
    """
    Automatically find saga_cmd.exe on Windows.
    Prefers saga7 (v7.x) over older versions.
    Searches within C:\\ recursively - may take a few seconds on first import.

    Returns:
    --------
    str - full path to saga_cmd.exe

    Raises:
    -------
    FileNotFoundError if no SAGA installation is found
    """
    for pattern in [r"C:\**\saga7\saga_cmd.exe",
                    r"C:\**\saga\saga_cmd.exe"]:
        candidates = glob.glob(pattern, recursive=True)
        if candidates:
            print(f"SAGA found: {candidates[0]}")
            return candidates[0]
    raise FileNotFoundError(
        "saga_cmd.exe not found. "
        "Please install QGIS (includes SAGA) or standalone SAGA GIS."
    )

SAGA_CMD = _find_saga_cmd()

# Add SAGA and QGIS bin directories to PATH so SAGA can find its DLLs
_saga_dir  = os.path.dirname(SAGA_CMD)
_qgis_bin  = os.path.normpath(os.path.join(_saga_dir, "..", "..", "bin"))
os.environ["PATH"] = _saga_dir + ";" + _qgis_bin + ";" + os.environ["PATH"]

# Frozen environment copy --> pass this to all subprocess calls involving SAGA
SAGA_ENV = os.environ.copy()