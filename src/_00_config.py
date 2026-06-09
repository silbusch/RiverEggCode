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
