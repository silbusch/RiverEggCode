# =======================================================================================
# 2.3 Extracting/Sampling raster values to SWORD reaches
# =======================================================================================
# RASTER JOIN – width-based buffer (m)
RASTER_BUFFER_OFFSET_M  = 50  # fixed offset for SWORD positional uncertainty
RASTER_BUFFER_MIN_M = 50 # minimum buffer even for very narrow reaches
RASTER_BUFFER_MAX_M = 500 # maximum buffer to avoid over-extraction
RASTER_NODATA_THRESHOLD = -9999  # pixels with this value are ignored

# =======================================================================================
# 3. EGG CODE CLASSIFICATION THRESHOLDS ----> NOTE: EXAMPLE for clipped SWORD
# =======================================================================================

#-------------------------------------------------------------------------
# Classes based on SWORD dataset (2026 University of North Carolina at Chapel Hill)
# SL – Slope classes (1–5)
# SWORD stores slope in permille (‰), not m/m
# Based on data distribution (min=0, p25=2.9, p50=5.1, p75=9.5, max=249)
# Breaks chosen to reflect geomorphic meaningful thresholds in ‰:
SLOPE_BREAKS = [0.0, 2.0, 5.0, 10.0, 30.0, float("inf")]
SLOPE_LABELS = [1,   2,   3,    4,     5]

# SL=1: very low  < 2‰   → lowland / floodplain
# SL=2: low       2–5‰   → piedmont
# SL=3: moderate  5–10‰  → transition
# SL=4: high      10–30‰ → mountain
# SL=5: very high > 30‰  → steep / cascade

# P – Planform (based on n_chan_mod from SWORD)
# n_chan_mod = modelled number of channels
# 75% of reaches = 1.0 → single channel dominates
PLANFORM_SINGLE_MAX   = 1.2   # ≤ 1.2 → straight or meandering (St/Me)
PLANFORM_BRAIDED_MAX  = 2.0   # 1.2–2.0 → braided (Br)
                               # > 2.0 → anabranching (An)

# QT – Discharge class (based on facc = flow accumulation from SOWRD)
# Using quantiles so classes adapt to the study area automatically
# min=73, p25=1399, p50=4365, p75=32119, max=59497
QT_BREAKS = [0, 1399, 4365, 32119, 59496, float("inf")]
QT_LABELS = [1, 2,    3,    4,     5]
# QT=1: very low   < p25
# QT=2: low        p25–p50
# QT=3: medium     p50–p75
# QT=4: high       p75–max
# QT=5: very high  > max (future reaches outside current range)

# TM – Sediment transport mode (derived from slope in ‰)
TM_BEDLOAD_SLOPE_MIN   = 5.0   # slope > 5‰  → bedload dominated
TM_SUSPENDED_SLOPE_MAX = 2.0   # slope < 2‰  → suspended dominated
                                # between     → mixed

# WD – Width/Depth ratio
# NOTE: wse = water surface elevation (m above sea level), NOT depth
# -> WD ratio cannot be computed from SWORD alone
# -> Flagged as NOT AVAILABLE until a depth dataset is joined
WD_AVAILABLE = False
WD_THRESHOLD = 12.0   # kept for future use (Rosgen 1994)
#-------------------------------------------------------------------------
