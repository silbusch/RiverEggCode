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
#from _00_config import WD_AVAILABLE

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


# class TransportModeClassifier(EggClassifier):
#     name = ""
#     source_col = ""
#     breaks = [,float("inf")]
#     labels = []

#     def classify(self, gdf):
#         """
#         Classify sediment transport mode based on ....
#         """
# ============================================================
# RIVER PROFILES
# Study area specific classifier configurations.
# Adding new profiles here for rivers with different characteristics.
# ============================================================

# randome rules for testing
# Lowland profile for low-gradient rivers (e.g. Elbe, Rhine)
# Uses finer slope breaks to better discriminate lowland reaches
# NOTE: breaks are placeholders adjust after data exploration
class SlopeClassifierLowland(SlopeClassifier):
    """
    Slope classifier for lowland rivers.
    Finer breaks for low-gradient environments.
    Inherits everything from SlopeClassifier except breaks and labels.
    """
    breaks = [0.0, 0.5, 1.0, 2.0, 5.0, float("inf")]
    labels = [1, 2, 3, 4, 5]


# ============================================================
# CLASSIFIER REGISTRY
# Adding new classifiers here to include them in classify_all().
# For aoi specific profiles, creating a new list below.
# ============================================================
# Default profile: applies to all rivers unless specified
DEFAULT_CLASSIFIERS = [
    SlopeClassifier(),
    PlanformClassifier(),
    DischargeClassifier(),
]

LOWLAND_CLASSIFIERS = [
    SlopeClassifierLowland(),  # finer slope breaks for lowland
    PlanformClassifier(),      # identical to default
    DischargeClassifier(),     # identical to default
]




def classify_all(gdf, classifiers=DEFAULT_CLASSIFIERS):
    """
    Run all available classifiers on a GeoDataFrame.
    Classifiers are defined in DEFAULT_CLASSIFIERS registry.
    To use a study-area specific profile, pass a different list.
    
    Parameters:
    -----------
    gdf : GeoDataFrame - SWORD reaches with joined attributes
    classifiers : list - list of EggClassifier instances to run

    Returns:
    --------
    GeoDataFrame with new egg_ columns added
    """
    result = gdf.copy()
    
    for classifier in classifiers:
        if not classifier.available: # check attribute of single classifier
            continue
        if not classifier.validate(result): # check if source_col exists
            continue
        result[classifier.name] = classifier.classify(result)
        print(f" {classifier.name}: Done")

    return result