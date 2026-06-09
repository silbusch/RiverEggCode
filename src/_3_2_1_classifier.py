# src/_3_2_1_classifier.py
# ============================================================
# EGG CODE CLASSIFICATION FUNCTIONS
#
# Every egg dimension is implemented as a subclass of EggClassifier.
# The base class defines the interface (classify, validate, name,
# source_col, available). Subclasses override only what changes.
#
# Current classifiers:
#   SlopeClassifier     -> egg_SL (source: slope)
#   PlanformClassifier  -> egg_P  (source: n_chan_mod)
#   DischargeClassifier -> egg_QT (source: facc)
#
# ============================================================

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))
from _00_config import WD_AVAILABLE

# NOTE: Label format decision pending supervisor review
# Option A: Integer labels (1-5) for ordinal classes (SL, QT) 
#           --> enables mathematical operations (mean, sort)
# Option B: String labels ("low", "high") for all classes
#           --> more readable in app and egg output...with math in the background?

class EggClassifier:
    """
    Base class for all EggCode dimension classifiers.
    
    Every classifier that adds an egg_ column to the SWORD GeoDataFrame
    must inherit from this class and implement the classify() method.
    
    Attributes:
    -----------
    name       : str  - output column name (e.g. "egg_SL"), the name for the Egg row
    source_col : str  - input column from SWORD with the needed feature for the egg (e.g. "slope") 
    available  : bool - if False, classifier is skipped in classify_all()
    """

    name       = None # must be overridden by subclass
    source_col = None # must be overridden by subclass
    available  = True # can be set to False if data is missing

    def classify(self, gdf):
        """
        Classify each SWORD reach and return a pandas Series.
        Must be overridden by every subclass.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement classify()"
        )

    def validate(self, gdf):
        """
        Check if source_col exists in the GeoDataFrame before classifying.
        Returns True if ready, False if source column is missing.
        """
        if self.source_col not in gdf.columns:
            print(f"  {self.name}: source column '{self.source_col}' not found --> skipping")
            return False
        return True



class SlopeClassifier(EggClassifier):
    name = "egg_SL"
    source_col = "slope"
    breaks = [0.0, 2.0, 5.0, 10.0, 30.0, float("inf")] # NOTE: random placeholder
    labels = [1, 2, 3, 4, 5]

    def classify(self, gdf):
        """
        Classify slope into interger classes.
        SWORD stores slope in permille.
        Breaks defined in config.py -> SLOPE_BREAKS.

        Returns: pd.Series of int, NaN where slope is missing.
        """
        return pd.cut(
            gdf[self.source_col],
            bins=self.breaks,
            labels=self.labels,
            include_lowest=True
        ).astype("Int64")


class PlanformClassifier(EggClassifier):
    name = "egg_PL"
    source_col = "n_chan_mod"
    #NOTE: need to check dimensions of global n_chan_mod
    single_max = 1.2   # <= single channel, just example
    braided_max = 2.0   # <= braided, > single_max , change in future
                           # > braided_max → anabranching  

    def classify(self, gdf):
        """
        Classify planform based on modelled number of channels.
        St/Me = single channel, Br = braided, An = anabranching...etc.
        """
        conditions = [
            gdf[self.source_col] <= self.single_max,
            (gdf[self.source_col] > self.single_max) & (gdf[self.source_col] <= self.braided_max),
            gdf[self.source_col] > self.braided_max
        ]
        choices = ["St", "Br", "An"]

        return pd.Series(
            np.select(conditions, choices, default=pd.NA),
            index=gdf.index,
            dtype="string"
        )        


class DischargeClassifier(EggClassifier):
    name = "egg_QT"
    source_col = "facc"
    breaks = [0, 1399, 4365, 32119, 59496, float("inf")] # NOTE: random placeholder
    labels = ["1", "more water!", "3","woooow", "lalal"]

    def classify(self, gdf):
        """
        Classify flow accumulation into discharge classes (e.g. QT 1 to 5)....adjust in future
        """
        return pd.cut(
            gdf[self.source_col],
            bins=self.breaks,
            labels=self.labels,
            include_lowest=True
        ).astype("string")


class TransportModeClassifier(EggClassifier):
    name = ""
    source_col = ""
    breaks = [,float("inf")]
    labels = []

    def classify(self, gdf):
        """
        Classify sediment transport mode based on ....
        """









# def classify_all(gdf):
#     """
#     Run all available classifiers on a GeoDataFrame.
#     Returns the GeoDataFrame with new Egg Code columns added.

#     New columns:
#         egg_SL – Slope class (Int64)
#         egg_P – Planform (string: St/Br/An)
#         egg_QT – Discharge class (Int64)
#         egg_TM – Transport mode (string: Bl/Mx/Su)
#         egg_WD – Width/Depth (string: not available → NaN)
#     """
#     result = gdf.copy()

# # NOTE: Still hardcoded!!!!
#     result["egg_SL"] = classify_slope(result)
#     result["egg_P"] = classify_planform(result)
#     result["egg_QT"] = classify_discharge(result)
#     result["egg_TM"] = classify_transport_mode(result)

#     # WD not available until depth dataset is joined or fitting datasend is found...
#     if not WD_AVAILABLE:
#         result["egg_WD"] = pd.NA
#         print("  egg_WD : not available (no depth dataset joined)")

#     print("Classification complete:")
#     print(f"egg_SL : {result['egg_SL'].value_counts().sort_index().to_dict()}")
#     print(f"egg_P : {result['egg_P'].value_counts().to_dict()}")
#     print(f"egg_QT : {result['egg_QT'].value_counts().sort_index().to_dict()}")
#     print(f"egg_TM : {result['egg_TM'].value_counts().to_dict()}")

#     return result