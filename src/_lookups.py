# src/_lookups.py
# ============================================================
# CLASS DESCRIPTION LOOKUP TABLES
#
# Maps integer Egg class codes to human-readable descriptions.
# Used in two contexts:
#   1. Streamlit app: to generate text descriptions of river reaches
#      when a user clicks on a reach or Egg on the map
#   2. Notebook 03: for exploratory analysis and reporting
#
# Structure:
#   Each dictionary maps integer class codes --> description strings.
#   Descriptions follow the format: "dimension1 | dimension2 | ..."
#   matching the multi-digit class code structure of each sub-classification.
#
# Sources:
#   GloRiC v1.0 - Ouellet Dallaire et al. (2019)
#   "A multidisciplinary framework to derive global river reach
#    classifications at high spatial resolution"
#   Environmental Research Letters. DOI: 10.1088/1748-9326/aad8e9
#
# How to add a new lookup table:
#   1. Define a new dictionary following the naming convention:
#      {EGG_DIMENSION}_CLASS_LOOKUP  (e.g. SLOPE_CLASS_LOOKUP)
#   2. Map each integer class code to a descriptive string
#   3. Import the dictionary in both _3_2_1_classifier.py and app/app.py
#
# NOTE: class codes are stored as integers in SWORD after joining.
#       Keys in these dictionaries must therefore be integers, not strings.
# ============================================================


# ============================================================
# egg_HY - Hydrologic sub-classification (GloRiC)
# Two-digit code: variability (1st) + discharge magnitude (2nd)
# 15 classes total (3 variability levels × 5 discharge levels)
# ============================================================
HYDR_CLASS_LOOKUP = {
    # Low variability (flow regime variability index V < 2)
    11: "low variability | very low discharge (0.1-10 m³/s)",
    12: "low variability | low discharge (10-100 m³/s)",
    13: "low variability | medium discharge (100-1,000 m³/s)",
    14: "low variability | high discharge (1,000-10,000 m³/s)",
    15: "low variability | very high discharge (>10,000 m³/s)",
    # Medium variability (2 ≤ V < 3)
    21: "medium variability | very low discharge (0.1-10 m³/s)",
    22: "medium variability | low discharge (10-100 m³/s)",
    23: "medium variability | medium discharge (100-1,000 m³/s)",
    24: "medium variability | high discharge (1,000-10,000 m³/s)",
    25: "medium variability | very high discharge (>10,000 m³/s)",
    # High variability (V ≥ 3)
    31: "high variability | very low discharge (0.1-10 m³/s)",
    32: "high variability | low discharge (10-100 m³/s)",
    33: "high variability | medium discharge (100-1,000 m³/s)",
    34: "high variability | high discharge (1,000-10,000 m³/s)",
    35: "high variability | very high discharge (>10,000 m³/s)",
}


# ============================================================
# egg_PHY - Physio-climatic sub-classification (GloRiC)
# Three-digit code: temperature (1st) + CMI (2nd) + elevation (3rd)
# 24 classes total (4 temperature × 3 CMI × 2 elevation levels)
# CMI = Climate Moisture Index = (precipitation/PET) - 1
# ============================================================
PHYS_CLASS_LOOKUP = {
    # Low temperature
    111: "low temperature | low CMI | low elevation",
    112: "low temperature | low CMI | high elevation",
    121: "low temperature | medium CMI | low elevation",
    122: "low temperature | medium CMI | high elevation",
    131: "low temperature | high CMI | low elevation",
    132: "low temperature | high CMI | high elevation",
    # Medium temperature
    211: "medium temperature | low CMI | low elevation",
    212: "medium temperature | low CMI | high elevation",
    221: "medium temperature | medium CMI | low elevation",
    222: "medium temperature | medium CMI | high elevation",
    231: "medium temperature | high CMI | low elevation",
    232: "medium temperature | high CMI | high elevation",
    # High temperature
    311: "high temperature | low CMI | low elevation",
    312: "high temperature | low CMI | high elevation",
    321: "high temperature | medium CMI | low elevation",
    322: "high temperature | medium CMI | high elevation",
    331: "high temperature | high CMI | low elevation",
    332: "high temperature | high CMI | high elevation",
    # Very high temperature
    411: "very high temperature | low CMI | low elevation",
    412: "very high temperature | low CMI | high elevation",
    421: "very high temperature | medium CMI | low elevation",
    422: "very high temperature | medium CMI | high elevation",
    431: "very high temperature | high CMI | low elevation",
    432: "very high temperature | high CMI | high elevation",
}


# ============================================================
# egg_LW - Lake-wetland and stream power classification (GloRiC)
# Two-digit code: lake-wetland influence (1st) + stream power (2nd)
# 4 classes total
# ============================================================
LAKE_WET_CLASS_LOOKUP = {
    11: "no lakes or wetlands | low stream power",
    12: "no lakes or wetlands | high stream power",
    21: "lake-wetland influenced | low stream power",
    22: "lake-wetland influenced | high stream power",
}


# ============================================================
# egg_GE - Combined geomorphic reach type (GloRiC)
# Three-digit code combining physio-climatic, hydrologic
# and geomorphic sub-classifications into 127 river reach types.
# Only classes observed globally in GloRiC v1.0 are listed here.
# Full table: GloRiC v1.0 Technical Documentation, Table S1.
# ============================================================
GEOM_CLASS_LOOKUP = {
    # Region 1 - cold, low and medium moisture
    111: "cold, low/medium moisture | very small river | low stream power",
    112: "cold, low/medium moisture | very small river | medium/high stream power",
    113: "cold, low/medium moisture | very small river | lake-wetland influenced",
    121: "cold, low/medium moisture | small river | low stream power",
    122: "cold, low/medium moisture | small river | medium/high stream power",
    123: "cold, low/medium moisture | small river | lake-wetland influenced",
    131: "cold, low/medium moisture | medium river | low stream power",
    132: "cold, low/medium moisture | medium river | medium/high stream power",
    133: "cold, low/medium moisture | medium river | lake-wetland influenced",
    141: "cold, low/medium moisture | large river | low stream power",
    142: "cold, low/medium moisture | large river | medium/high stream power",
    143: "cold, low/medium moisture | large river | lake-wetland influenced",
    150: "cold, low/medium moisture | very large river",
    # Region 2 - cold, high moisture
    211: "cold, high moisture | very small river | low stream power",
    212: "cold, high moisture | very small river | medium/high stream power",
    213: "cold, high moisture | very small river | lake-wetland influenced",
    221: "cold, high moisture | small river | low stream power",
    222: "cold, high moisture | small river | medium/high stream power",
    223: "cold, high moisture | small river | lake-wetland influenced",
    231: "cold, high moisture | medium river | low stream power",
    232: "cold, high moisture | medium river | medium/high stream power",
    233: "cold, high moisture | medium river | lake-wetland influenced",
    241: "cold, high moisture | large river | low stream power",
    242: "cold, high moisture | large river | medium/high stream power",
    243: "cold, high moisture | large river | lake-wetland influenced",
    250: "cold, high moisture | very large river",
    # Region 3 - warm and hot, low moisture
    311: "warm/hot, low moisture | very small river | low stream power",
    312: "warm/hot, low moisture | very small river | medium/high stream power",
    313: "warm/hot, low moisture | very small river | lake-wetland influenced",
    321: "warm/hot, low moisture | small river | low stream power",
    322: "warm/hot, low moisture | small river | medium/high stream power",
    323: "warm/hot, low moisture | small river | lake-wetland influenced",
    331: "warm/hot, low moisture | medium river | low stream power",
    332: "warm/hot, low moisture | medium river | medium/high stream power",
    333: "warm/hot, low moisture | medium river | lake-wetland influenced",
    341: "warm/hot, low moisture | large river | low stream power",
    342: "warm/hot, low moisture | large river | medium/high stream power",
    343: "warm/hot, low moisture | large river | lake-wetland influenced",
    350: "warm/hot, low moisture | very large river",
    # Region 4 - warm, medium moisture
    411: "warm, medium moisture | very small river | low stream power",
    412: "warm, medium moisture | very small river | medium/high stream power",
    413: "warm, medium moisture | very small river | lake-wetland influenced",
    421: "warm, medium moisture | small river | low stream power",
    422: "warm, medium moisture | small river | medium/high stream power",
    423: "warm, medium moisture | small river | lake-wetland influenced",
    431: "warm, medium moisture | medium river | low stream power",
    432: "warm, medium moisture | medium river | medium/high stream power",
    433: "warm, medium moisture | medium river | lake-wetland influenced",
    441: "warm, medium moisture | large river | low stream power",
    442: "warm, medium moisture | large river | medium/high stream power",
    443: "warm, medium moisture | large river | lake-wetland influenced",
    450: "warm, medium moisture | very large river",
    # Region 5 - warm, high moisture
    511: "warm, high moisture | very small river | low stream power",
    512: "warm, high moisture | very small river | medium/high stream power",
    513: "warm, high moisture | very small river | lake-wetland influenced",
    521: "warm, high moisture | small river | low stream power",
    522: "warm, high moisture | small river | medium/high stream power",
    523: "warm, high moisture | small river | lake-wetland influenced",
    531: "warm, high moisture | medium river | low stream power",
    532: "warm, high moisture | medium river | medium/high stream power",
    533: "warm, high moisture | medium river | lake-wetland influenced",
    541: "warm, high moisture | large river | low stream power",
    542: "warm, high moisture | large river | medium/high stream power",
    543: "warm, high moisture | large river | lake-wetland influenced",
    550: "warm, high moisture | very large river",
    # Region 6 - hot, high moisture
    611: "hot, high moisture | very small river | low stream power",
    612: "hot, high moisture | very small river | medium/high stream power",
    613: "hot, high moisture | very small river | lake-wetland influenced",
    621: "hot, high moisture | small river | low stream power",
    622: "hot, high moisture | small river | medium/high stream power",
    623: "hot, high moisture | small river | lake-wetland influenced",
    631: "hot, high moisture | medium river | low stream power",
    632: "hot, high moisture | medium river | medium/high stream power",
    633: "hot, high moisture | medium river | lake-wetland influenced",
    641: "hot, high moisture | large river | low stream power",
    642: "hot, high moisture | large river | medium/high stream power",
    643: "hot, high moisture | large river | lake-wetland influenced",
    650: "hot, high moisture | very large river",
    # Region 7 - very hot, low moisture
    711: "very hot, low moisture | very small river | low stream power",
    712: "very hot, low moisture | very small river | medium/high stream power",
    713: "very hot, low moisture | very small river | lake-wetland influenced",
    721: "very hot, low moisture | small river | low stream power",
    722: "very hot, low moisture | small river | medium/high stream power",
    723: "very hot, low moisture | small river | lake-wetland influenced",
    731: "very hot, low moisture | medium river | low stream power",
    732: "very hot, low moisture | medium river | medium/high stream power",
    733: "very hot, low moisture | medium river | lake-wetland influenced",
    741: "very hot, low moisture | large river | low stream power",
    742: "very hot, low moisture | large river | medium/high stream power",
    743: "very hot, low moisture | large river | lake-wetland influenced",
    750: "very hot, low moisture | very large river",
    # Region 8 - very hot, high moisture
    811: "very hot, high moisture | very small river | low stream power",
    812: "very hot, high moisture | very small river | medium/high stream power",
    813: "very hot, high moisture | very small river | lake-wetland influenced",
    821: "very hot, high moisture | small river | low stream power",
    822: "very hot, high moisture | small river | medium/high stream power",
    823: "very hot, high moisture | small river | lake-wetland influenced",
    831: "very hot, high moisture | medium river | low stream power",
    832: "very hot, high moisture | medium river | medium/high stream power",
    833: "very hot, high moisture | medium river | lake-wetland influenced",
    841: "very hot, high moisture | large river | low stream power",
    842: "very hot, high moisture | large river | medium/high stream power",
    843: "very hot, high moisture | large river | lake-wetland influenced",
    850: "very hot, high moisture | very large river",
    # Region 9 - cold and warm, high elevation
    911: "cold/warm, high elevation | very small river | low stream power",
    912: "cold/warm, high elevation | very small river | medium/high stream power",
    913: "cold/warm, high elevation | very small river | lake-wetland influenced",
    921: "cold/warm, high elevation | small river | low stream power",
    922: "cold/warm, high elevation | small river | medium/high stream power",
    923: "cold/warm, high elevation | small river | lake-wetland influenced",
    931: "cold/warm, high elevation | medium river | low stream power",
    932: "cold/warm, high elevation | medium river | medium/high stream power",
    933: "cold/warm, high elevation | medium river | lake-wetland influenced",
    941: "cold/warm, high elevation | large river | low stream power",
    942: "cold/warm, high elevation | large river | medium/high stream power",
    # Region 10 - hot and very hot, high elevation
    1011: "hot/very hot, high elevation | very small river | low stream power",
    1012: "hot/very hot, high elevation | very small river | medium/high stream power",
    1013: "hot/very hot, high elevation | very small river | lake-wetland influenced",
    1021: "hot/very hot, high elevation | small river | low stream power",
    1022: "hot/very hot, high elevation | small river | medium/high stream power",
    1023: "hot/very hot, high elevation | small river | lake-wetland influenced",
    1031: "hot/very hot, high elevation | medium river | low stream power",
    1032: "hot/very hot, high elevation | medium river | medium/high stream power",
    1033: "hot/very hot, high elevation | medium river | lake-wetland influenced",
    1041: "hot/very hot, high elevation | large river | low stream power",
    1042: "hot/very hot, high elevation | large river | medium/high stream power",
    1043: "hot/very hot, high elevation | large river | lake-wetland influenced",
}


# ============================================================
# egg_SL - Slope classification
# Source: computed from SWORD slope column in _3_2_1_classifier.py
# NOTE: thresholds are currently placeholders calibrated for Naryn -
#       global calibration pending supervisor review
# ============================================================
SLOPE_CLASS_LOOKUP = {
    1: "very low gradient (< 2 m/km)",
    2: "low gradient (2-5 m/km)",
    3: "moderate gradient (5-10 m/km)",
    4: "high gradient (10-30 m/km)",
    5: "very high gradient (> 30 m/km)",
}


# ============================================================
# egg_PL - Planform classification
# Source: computed from SWORD n_chan_mod column
# NOTE: thresholds (single_max, braided_max) are placeholders -
#       global calibration of n_chan_mod dimensions pending
# ============================================================
PLANFORM_CLASS_LOOKUP = {
    "St": "single thread (n_chan_mod ≤ 1.2)",
    "Br": "braided (1.2 < n_chan_mod ≤ 2.0)",
    "An": "anabranching (n_chan_mod > 2.0)",
}

# ============================================================
# egg_QT - Discharge classification
# Source: computed from SWORD facc column in _3_2_1_classifier.py
# NOTE: breaks are currently Naryn-specific placeholders based on
#       quantiles of facc values - global calibration pending.
#       Label meaning (1=low ... 5=very high) to be confirmed
#       with supervisor before finalizing....AND WHAT ABOUT THE DISCHARGE PROFILE???

# # Alternativ aus Variablen von z.B. RiverATLAS:
# dis_m3_pyr  - mittlerer Jahresabfluss
# dis_m3_pmn  - mittlerer Monatsabfluss (niedrigster Monat)
# dis_m3_pmx  - mittlerer Monatsabfluss (höchster Monat)

# oder aus GloRiC:
# Log_Q_var   - Flow Variability Index = max. monatlicher Q / Jahresmittel
# Class_hydr  - bereits beide Dimensionen kombiniert (Mittelwert + Variabilität)

# ============================================================
DISCHARGE_CLASS_LOOKUP = {
    1: "very low discharge (facc quantile 1)",
    2: "low discharge (facc quantile 2)",
    3: "medium discharge (facc quantile 3)",
    4: "high discharge (facc quantile 4)",
    5: "very high discharge (facc quantile 5)",
}

# ============================================================
# Utility function - get description for any Egg dimension
# ============================================================

# Registry mapping egg column names to their lookup tables
EGG_LOOKUP_REGISTRY = {
    "egg_HY" : HYDR_CLASS_LOOKUP,
    "egg_PHY": PHYS_CLASS_LOOKUP,
    "egg_LW" : LAKE_WET_CLASS_LOOKUP,
    "egg_GE" : GEOM_CLASS_LOOKUP,
    "egg_SL" : SLOPE_CLASS_LOOKUP,
    "egg_PL" : PLANFORM_CLASS_LOOKUP,
    "egg_QT" : DISCHARGE_CLASS_LOOKUP,
}


def get_description(egg_col, class_code):
    """
    Return the human-readable description for a given Egg dimension
    and class code. Returns 'unknown' if no lookup table exists or
    if the class code is not found.

    Parameters:
    -----------
    egg_col    : str - Egg column name (e.g. 'egg_HY', 'egg_GE')
    class_code : int or str - class code value from the SWORD dataset

    Returns:
    --------
    str - human-readable description

    Example:
    --------
    get_description('egg_HY', 23)
    --> 'medium variability | medium discharge (100-1,000 m³/s)'
    """
    lookup = EGG_LOOKUP_REGISTRY.get(egg_col)
    if lookup is None:
        return f"no lookup table for {egg_col}"
    # Convert to int for lookup (values may be stored as float after join)
    try:
        key = int(class_code)
    except (ValueError, TypeError):
        return f"invalid class code: {class_code}"
    return lookup.get(key, f"unknown class {key}")