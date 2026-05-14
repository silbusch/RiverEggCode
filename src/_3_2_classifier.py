# src/_3_2_classifier.py
# ============================================================
# EGG CODE CLASSIFICATION FUNCTIONS
# Each function takes a GeoDataFrame and returns a new column.
# All operations are vectorized.
# NOTE: Classification Thresholds are read from config.py
# ============================================================

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))
from _00_config import (
    SLOPE_BREAKS, SLOPE_LABELS,
    PLANFORM_SINGLE_MAX, PLANFORM_BRAIDED_MAX,
    QT_BREAKS, QT_LABELS,
    TM_BEDLOAD_SLOPE_MIN, TM_SUSPENDED_SLOPE_MAX,
    WD_AVAILABLE
)


def classify_slope(gdf, col="slope"):
    """
    Classify slope into interger classes.
    SWORD stores slope in permille.
    Breaks defined in config.py -> SLOPE_BREAKS.

    Returns: pd.Series of int, NaN where slope is missing.
    """
    return pd.cut(
        gdf[col],
        bins=SLOPE_BREAKS,
        labels=SLOPE_LABELS,
        include_lowest=True
    ).astype("Int64")


def classify_planform(gdf, col="n_chan_mod"):
    """
    Classify planform based on modelled number of channels.
    St/Me = single channel, Br = braided, An = anabranching.
    Thresholds defined in config.py.

    Returns: pd.Series of str ("St", "Br", "An"), NaN where missing.
    """
    conditions = [
        gdf[col] <= PLANFORM_SINGLE_MAX,
        (gdf[col] > PLANFORM_SINGLE_MAX) & (gdf[col] <= PLANFORM_BRAIDED_MAX),
        gdf[col] > PLANFORM_BRAIDED_MAX
    ]
    choices = ["St", "Br", "An"]

    return pd.Series(
        np.select(conditions, choices, default=pd.NA),
        index=gdf.index,
        dtype="string"
    )


def classify_discharge(gdf, col="facc"):
    """
    Classify flow accumulation into discharge classes (e.g. QT 1–5).
    Breaks defined in config.py -> QT_BREAKS (quantile-based).

    Returns: pd.Series of int, NaN where facc is missing.
    """
    return pd.cut(
        gdf[col],
        bins=QT_BREAKS,
        labels=QT_LABELS,
        include_lowest=True
    ).astype("Int64")


def classify_transport_mode(gdf, col="slope"):
    """
    Classify sediment transport mode based on slope (in ‰).
    Bl = bedload dominated, Mx = mixed, Su = suspended load.
    Thresholds defined in config.py.

    Returns: pd.Series of str ("Bl", "Mx", "Su"), NaN where missing.
    """
    conditions = [
        gdf[col] >= TM_BEDLOAD_SLOPE_MIN,
        gdf[col] < TM_SUSPENDED_SLOPE_MAX
    ]
    choices = ["Bl", "Su"]

    return pd.Series(
        np.select(conditions, choices, default="Mx"),
        index=gdf.index,
        dtype="string"
    )


def classify_all(gdf):
    """
    Run all available classifiers on a GeoDataFrame.
    Returns the GeoDataFrame with new Egg Code columns added.

    New columns:
        egg_SL – Slope class (Int64)
        egg_P – Planform (string: St/Br/An)
        egg_QT – Discharge class (Int64)
        egg_TM – Transport mode (string: Bl/Mx/Su)
        egg_WD – Width/Depth (string: not available → NaN)
    """
    result = gdf.copy()

    result["egg_SL"] = classify_slope(result)
    result["egg_P"] = classify_planform(result)
    result["egg_QT"] = classify_discharge(result)
    result["egg_TM"] = classify_transport_mode(result)

    # WD not available until depth dataset is joined or fitting datasend is found...
    if not WD_AVAILABLE:
        result["egg_WD"] = pd.NA
        print("  egg_WD : not available (no depth dataset joined)")

    print("Classification complete:")
    print(f"egg_SL : {result['egg_SL'].value_counts().sort_index().to_dict()}")
    print(f"egg_P : {result['egg_P'].value_counts().to_dict()}")
    print(f"egg_QT : {result['egg_QT'].value_counts().sort_index().to_dict()}")
    print(f"egg_TM : {result['egg_TM'].value_counts().to_dict()}")

    return result