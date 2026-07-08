# src/_00_setup.py
# ============================================================
# STUDY AREA SETUP
#
# Loads and prepares the two base datasets for any study area:
#   1. HydroBASINS Level 5 polygon --> AOI boundary + bbox
#   2. SWORD reaches --> filtered to study area via PFAF_ID
#
# All downstream functions (DEM download, raster join, line join,
# classification) use the outputs of setup_study_area() as their
# spatial reference.
#
# Configuration (PFAF_IDS, PFAF_LEVEL_DIGITS) comes from _00_config.py.
# Paths (IN_SWORD, IN_BASIN_5) come from _0_config_paths.py.
# This file contains ONLY loading and filtering logic.
#
# Usage in notebooks:
#   from _00_setup import setup_study_area
#   from _0_config_paths import IN_SWORD, IN_BASIN_5
#   from _00_config import PFAF_IDS, PFAF_LEVEL_DIGITS
#
#   aoi, sword = setup_study_area(IN_BASIN_5, IN_SWORD,
#                                  PFAF_IDS, PFAF_LEVEL_DIGITS)
#   bbox = tuple(aoi.total_bounds)
# ============================================================

import geopandas as gpd
import os


def setup_study_area(basin_path, sword_path, pfaf_ids, pfaf_level_digits):
    """
    Load and filter HydroBASINS Level 5 and SWORD reaches to the
    study area defined by PFAF_IDS.

    Parameters:
    -----------
    basin_path        : str  - path to HydroBASINS Level 5 GeoPackage
                               (IN_BASIN_5 from _0_config_paths.py)
    sword_path        : str  - path to continental SWORD GeoPackage
                               (IN_SWORD from _0_config_paths.py,
                                auto-selected from PFAF_IDS via CONTINENT)
    pfaf_ids          : list - list of 5-digit PFAF_IDs (from _00_config.py)
                               e.g. [46219] for the Naryn River
    pfaf_level_digits : int  - number of digits in PFAF_ID (must be 5)
                               Warning is printed if not 5.

    Returns:
    --------
    aoi   : GeoDataFrame - dissolved HydroBASINS polygon for study area
            --> use aoi.total_bounds as bbox for all download functions
    sword : GeoDataFrame - SWORD reaches filtered to study area
            --> first pfaf_level_digits digits of reach_id match pfaf_ids

    Raises:
    -------
    ValueError if no basins or reaches are found for the given PFAF_IDs.
    """

    # --------------------------------------------------------
    # Validate PFAF configuration
    # --------------------------------------------------------
    if pfaf_level_digits != 5:
        print(
            f"WARNING: PFAF_LEVEL_DIGITS is {pfaf_level_digits} but must be 5 "
            f"for HydroBASINS Level 5. Check _00_config.py."
        )
    for pid in pfaf_ids:
        if len(str(pid)) != 5:
            print(
                f"WARNING: PFAF_ID {pid} is not 5 digits. "
                f"HydroBASINS Level 5 requires exactly 5-digit PFAF_IDs "
                f"(e.g. 46219). Check _00_config.py."
            )

    # --------------------------------------------------------
    # Step 1: Load HydroBASINS Level 5 and filter to PFAF_IDs
    # --------------------------------------------------------
    print(f"Loading HydroBASINS Level 5 from: {basin_path}")
    basins_all = gpd.read_file(basin_path)
    aoi = basins_all[basins_all["PFAF_ID"].isin(pfaf_ids)].copy()

    if len(aoi) == 0:
        raise ValueError(
            f"No basins found for PFAF_IDs: {pfaf_ids}. "
            f"Check IN_BASIN_5 in _0_config_paths.py and "
            f"PFAF_IDS in _00_config.py."
        )

    print(f"Basin polygons found: {len(aoi)} for PFAF_IDs: {pfaf_ids}")

    # Dissolve multiple basins into a single AOI polygon
    if len(aoi) > 1:
        aoi = aoi.dissolve().reset_index(drop=True)
        print(f"Dissolved {len(pfaf_ids)} basins into single AOI polygon")

    bbox = aoi.total_bounds  # (minx, miny, maxx, maxy)
    print(f"AOI bbox: {bbox}")

    # --------------------------------------------------------
    # Step 2: Load SWORD and filter to study area
    # --------------------------------------------------------
    print(f"\nLoading SWORD from: {sword_path}")

    # Use bbox for fast spatial pre-filter before PFAF_ID string filter
    sword_all = gpd.read_file(sword_path, bbox=tuple(bbox))
    print(f"SWORD reaches in bbox: {len(sword_all)}")

    # Filter by PFAF_ID encoded in reach_id
    # reach_id format: CBBBBBRRRRT
    #   C      = Continent digit
    #   BBBBB  = Pfafstetter basin digits up to Level 6
    #   --> first 5 digits (CBBBBB truncated to 5) = PFAF_ID Level 5
    sword = sword_all[
        sword_all["reach_id"]
        .astype(str)
        .str[:pfaf_level_digits]
        .astype(int)
        .isin(pfaf_ids)
    ].copy()

    print(f"SWORD reaches after PFAF_ID filter: {len(sword)}")

    if len(sword) == 0:
        raise ValueError(
            f"No SWORD reaches found for PFAF_IDs: {pfaf_ids}. "
            f"Check IN_SWORD in _0_config_paths.py."
        )

    return aoi, sword