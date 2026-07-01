# =======================================================================================
# In this configuration file, the study area for investigating single Riversystems is set.
# Setting single river systems as AOI is only to investigate the SWORD dataset and to search
# for erros, or compute the best global solutions for the river classes.
# =======================================================================================

# ============================================================
# STUDY AREA --> change here to switch rivers globally
# All notebooks and path configs derive from these two variables.
# ============================================================
# Setting the study area
# NOTE: A global Option, or C´continent option should be possible to produce all the data in the end.
# Later "global" will be used, to create ""
STUDY_AREA = "naryn"

# Pfafstetter Level-5 or Level-6 codes (first 5 or 6 digits of SWORD reach_id)
PFAF_IDS = [46219]

# Number of digits to use for PFAF matching (5 = Level 5, 6 = Level 6)
PFAF_LEVEL_DIGITS = 5

# #---- ELBE -------
# STUDY_AREA = "elbe"
# PFAF_IDS = [2328]
# PFAF_LEVEL_DIGITS = 4

# #---- AMAZON -------
# STUDY_AREA = "amazon"
# # PFAF_IDS = [62244, 62292, 62262] # just partly?
# # PFAF_LEVEL_DIGITS = 5


# =======================================================================================
# 2.3 Extracting/Sampling raster values to SWORD reaches
# =======================================================================================
# RASTER JOIN – width-based buffer (m)
RASTER_BUFFER_OFFSET_M  = 50  # fixed offset for SWORD positional uncertainty
RASTER_BUFFER_MIN_M = 50 # minimum buffer even for very narrow reaches
RASTER_BUFFER_MAX_M = 500 # maximum buffer to avoid over-extraction
RASTER_NODATA_THRESHOLD = -9999  # pixels with this value are ignored





# WD – Width/Depth ratio
# NOTE: wse = water surface elevation (m above sea level), NOT depth
# -> WD ratio cannot be computed from SWORD alone
# -> Flagged as NOT AVAILABLE until a depth dataset is joined
WD_AVAILABLE = False
WD_THRESHOLD = 12.0   # kept for future use (Rosgen 1994)
#-------------------------------------------------------------------------
