# src/_00_config.py
# ============================================================
# STUDY AREA CONFIGURATION
#
# This is the SINGLE file to edit when switching study areas.
# All other files derive their configuration from these values.
#
# To switch to a new river:
#   1. Change STUDY_AREA to the new river name (lowercase)
#   2. Change PFAF_IDS to the correct 5-digit Pfafstetter Level-5 codes
#   3. Run all notebooks from top to bottom
#
# How to find PFAF_IDs for a river:
#   - Look at the first 5 digits of any SWORD reach_id for that river
#   - Or browse HydroBASINS Level 5 to identify the basin codes
#   - A river may span multiple basins --> list all codes in PFAF_IDS
#
# Examples:
#   Naryn River (Kyrgyzstan / Uzbekistan): PFAF_IDS = [46219]
#   Elbe River (Germany / Czech Republic): PFAF_IDS = [22541]
# ============================================================

STUDY_AREA        = "naryn"
PFAF_IDS          = [46219]
PFAF_LEVEL_DIGITS = 5   # must be 5 for HydroBASINS Level 5

# Reach types to include in analysis:
# 1 = river (standard river reaches)
# 3 = lake on river – kept because wide/braided sections are classified
#     as lake-type in SWORD due to their SWOT surface appearance.
#     Excluding type 3 would systematically remove the most morphologically
#     interesting reaches (channel widening, alluvial fans, braided sections).
REACH_TYPES_TO_KEEP = [1, 3]


# ============================================================
# 2.3 Raster Join Configuration
# ============================================================
# Width-based buffer for raster extraction (meters)
RASTER_BUFFER_OFFSET_M  = 50   # fixed offset for SWORD positional uncertainty
RASTER_BUFFER_MIN_M     = 50   # minimum buffer even for very narrow reaches
RASTER_BUFFER_MAX_M     = 500  # maximum buffer to avoid over-extraction
RASTER_NODATA_THRESHOLD = -9999  # pixels at or below this value are ignored


# ============================================================
# Width/Depth Ratio (egg_WD)
# ============================================================
# NOTE: wse = water surface elevation (m above sea level), NOT depth
# --> WD ratio cannot be computed from SWORD alone
# --> Flagged as NOT AVAILABLE until a depth dataset is joined
WD_AVAILABLE = False
WD_THRESHOLD = 12.0   # kept for future use (Rosgen 1994)