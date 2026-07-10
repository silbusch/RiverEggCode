# src/_3_1_1_copute_features.py
# ============================================================
# FEATURE COMPUTATION
#
# Computes new derived features for SWORD reaches that require
# more complex logic than simple thresholding. Results are added 
# as new columns to the SWORD GeoDataFrame, which are then 
# classified into egg_ categories by classifiers in _3_2_1_classifier.py.
#
#------------------------------------------------------------
# Current features:
#   build_sword_graph(): networkx graph from SWORD topology
#   compute_upstream_free_distance(): upstream_free_km per reach
#
# ============================================================
#NOTE: adding for connectivity dataset from: https://www.nature.com/articles/s41586-019-1111-9
# NOTE: creating three types of connectivity
import pandas as pd
import networkx as nx
import rasterio
import numpy as np
import os
from shapely.geometry import LineString, Point
import geopandas as gpd

def build_sword_graph(sword, direction="upstream"):
    """
    Build a directed graph from SWORD topology.

    Parameters:
    -----------
    sword     : GeoDataFrame - SWORD reaches with rch_id_up, rch_id_dn,
                n_rch_up, n_rch_dn columns
    direction : str - "upstream" uses rch_id_up/n_rch_up,
                       "downstream" uses rch_id_dn/n_rch_dn

    Returns:
    --------
    networkx.DiGraph - edges point in the given direction
    """
    if direction == "upstream":
        id_col = "rch_id_up"
        n_col = "n_rch_up"
    elif direction == "downstream":
        id_col = "rch_id_dn"
        n_col = "n_rch_dn"
    else:
        raise ValueError("direction must be 'upstream' or 'downstream'")

    G = nx.DiGraph()

    for _, row in sword.iterrows():
        reach_id = row["reach_id"]
        G.add_node(reach_id)

        if row[n_col] == 0:
            continue

        neighbor_ids = row[id_col].split()
        for nb_id in neighbor_ids:
            G.add_edge(reach_id, int(nb_id))

    print(f"Graph nodes: {G.number_of_nodes()}")
    print(f"Graph edges: {G.number_of_edges()}")

    return G


# ============================================================
# Using SAGA to calculate floodplain width, based on Mariams R-Code
# ============================================================

def compute_cross_sections(sword_gdf, dem_path, vd_path, hd_path, mrvbf_path,
                            n_sections=50, half_width_m=1500, 
                            points_per_transect=301,
                            crs_meters="EPSG:32643"):
    """
    Generate perpendicular cross-sections along SWORD reaches and extract
    VD, HD and MRVBF values along each transect.

    Equivalent to Steps 2-7 in the R floodplain delineation script.

    Method:
    -------
    1. Sample n_sections points along each SWORD reach
    2. For each point: compute flow direction from local reach geometry
    3. Draw a perpendicular transect of 2 * half_width_m
    4. Sample points_per_transect points along each transect
    5. Extract elevation, VD, HD, MRVBF at each point via rasterio

    Parameters:
    -----------
    sword_gdf          : GeoDataFrame - SWORD reaches (line geometries)
    dem_path           : str - path to COP30 DEM GeoTIFF
    vd_path            : str - path to Vertical Distance raster (SAGA output)
    hd_path            : str - path to Horizontal Distance raster (SAGA output)
    mrvbf_path         : str - path to MRVBF raster (SAGA output)
    n_sections         : int - number of cross-sections per reach (default: 50)
    half_width_m       : float - half-width of each transect in meters (default: 1500)
    points_per_transect: int - sample points per transect (default: 301)
    crs_meters         : str - projected CRS for distance calculations

    Returns:
    --------
    pd.DataFrame with columns:
        section_id, reach_id, distance, X, Y,
        elevation, vd, hd, mrvbf

    Notes:
    ------
    - half_width_m=1500 matches the original R script default
    - n_sections=50 generates transects equally spaced along each reach
    - Points at distance=0 are at the river centerline
    - Negative distances = left bank, positive = right bank
    - SWORD positional uncertainty (~50-200m) is compensated by
      finding the DEM minimum within 5m of the centerline point
      (following Garber et al. 2024)
    """
    # Reproject to metric CRS for distance calculations
    sword_m = sword_gdf.to_crs(crs_meters).copy()

    # Open all rasters once – keep open for the full loop
    rasters = {}
    raster_paths = {
        "elevation": dem_path,
        "vd"       : vd_path,
        "hd"       : hd_path,
        "mrvbf"    : mrvbf_path,
    }

    for name, path in raster_paths.items():
        rasters[name] = rasterio.open(path)

    all_rows = []
    section_counter = 0

    for _, reach in sword_m.iterrows():
        geom = reach.geometry
        reach_id = reach["reach_id"]
        reach_len = geom.length

        if reach_len == 0:
            continue

        # Sample n_sections points equally spaced along the reach
        sample_distances = np.linspace(0, reach_len, n_sections + 2)[1:-1]

        for i, dist_along in enumerate(sample_distances):
            section_counter += 1
            center_point = geom.interpolate(dist_along)

            # Compute flow direction from local reach geometry
            # Use a small segment around the sample point
            d1 = max(0, dist_along - 50)
            d2 = min(reach_len, dist_along + 50)
            p1 = geom.interpolate(d1)
            p2 = geom.interpolate(d2)

            dx = p2.x - p1.x
            dy = p2.y - p1.y
            norm = np.sqrt(dx**2 + dy**2)

            if norm == 0:
                continue

            # Perpendicular direction (rotate flow vector 90°)
            perp_x = -dy / norm
            perp_y =  dx / norm

            # Create transect endpoints
            cx, cy = center_point.x, center_point.y
            start = Point(cx + perp_x * half_width_m,
                         cy + perp_y * half_width_m)
            end   = Point(cx - perp_x * half_width_m,
                         cy - perp_y * half_width_m)
            transect = LineString([start, end])

            # Sample points along transect
            distances = np.linspace(-half_width_m, half_width_m,
                                    points_per_transect)
            sample_points = [transect.interpolate(
                (d + half_width_m) / (2 * half_width_m),
                normalized=True
            ) for d in distances]

            # Extract raster values at each point
            for j, (pt, d) in enumerate(zip(sample_points, distances)):
                row = {
                    "section_id": section_counter,
                    "reach_id"  : reach_id,
                    "distance"  : d,
                    "X"         : pt.x,
                    "Y"         : pt.y,
                }

                # Extract value from each raster
                for name, src in rasters.items():
                    try:
                        # Convert to raster CRS if needed
                        pt_raster = pt
                        if src.crs.to_epsg() != int(crs_meters.split(":")[-1]):
                            pt_wgs84 = gpd.GeoSeries(
                                [pt], crs=crs_meters
                            ).to_crs(src.crs).iloc[0]
                            pt_raster = pt_wgs84

                        val = list(src.sample(
                            [(pt_raster.x, pt_raster.y)]
                        ))[0][0]

                        # Mask nodata
                        if src.nodata is not None and val == src.nodata:
                            val = np.nan
                        row[name] = float(val)

                    except Exception:
                        row[name] = np.nan

                all_rows.append(row)

    # Close rasters
    for src in rasters.values():
        src.close()

    df = pd.DataFrame(all_rows)
    df = df.dropna(subset=["elevation"])

    print(f"Cross-sections generated: {df['section_id'].nunique()}")
    print(f"Total sample points: {len(df)}")

    return df

def find_breakpoints(cs_df):
    """
    Find threshold values for VD, HD and MRVBF from cross-section profiles.
    
    Equivalent to Step 3 in the R floodplain delineation script.
    For each cross-section, finds the point of maximum gradient change
    (breakpoint) for VD and HD, and minimum gradient for MRVBF.
    Final thresholds are the median of all cross-section breakpoints –
    making the method self-calibrating without manual threshold setting.

    Parameters:
    -----------
    cs_df : pd.DataFrame - output of compute_cross_sections()
            must contain columns: section_id, distance, vd, hd, mrvbf

    Returns:
    --------
    dict with keys:
        vd_max    : float - vertical distance threshold
        hd_max    : float - horizontal distance threshold
        mrvbf_min : float - MRVBF threshold
        breakpoints : pd.DataFrame - per-section breakpoint values
    """
    import pandas as pd
    import numpy as np

    records = []

    for section_id, group in cs_df.groupby("section_id"):
        group = group.sort_values("distance").copy()

        # Drop NaN rows for gradient computation
        g_vd    = group.dropna(subset=["vd"])
        g_hd    = group.dropna(subset=["hd"])
        g_mrvbf = group.dropna(subset=["mrvbf"])

        row = {"section_id": section_id}

        # VD breakpoint – distance of maximum absolute gradient
        if len(g_vd) >= 2:
            vd_grad = np.gradient(g_vd["vd"].values,
                                  g_vd["distance"].values)
            idx = np.argmax(np.abs(vd_grad))
            row["vd_break_dist"] = g_vd["distance"].iloc[idx]
            row["vd_break_val"]  = g_vd["vd"].iloc[idx]
        else:
            row["vd_break_dist"] = np.nan
            row["vd_break_val"]  = np.nan

        # HD breakpoint – distance of maximum absolute gradient
        if len(g_hd) >= 2:
            hd_grad = np.gradient(g_hd["hd"].values,
                                  g_hd["distance"].values)
            idx = np.argmax(np.abs(hd_grad))
            row["hd_break_dist"] = g_hd["distance"].iloc[idx]
            row["hd_break_val"]  = g_hd["hd"].iloc[idx]
        else:
            row["hd_break_dist"] = np.nan
            row["hd_break_val"]  = np.nan

        # MRVBF breakpoint – distance of minimum gradient
        # (valley bottom flatness increases toward channel)
        if len(g_mrvbf) >= 2:
            mrvbf_grad = np.gradient(g_mrvbf["mrvbf"].values,
                                     g_mrvbf["distance"].values)
            idx = np.argmin(mrvbf_grad)
            row["mrvbf_break_dist"] = g_mrvbf["distance"].iloc[idx]
            row["mrvbf_break_val"]  = g_mrvbf["mrvbf"].iloc[idx]
        else:
            row["mrvbf_break_dist"] = np.nan
            row["mrvbf_break_val"]  = np.nan

        records.append(row)

    breakpoints = pd.DataFrame(records)

    # Final thresholds = median of all cross-section breakpoints
    # Median is robust against outliers from noisy cross-sections
    vd_max    = float(breakpoints["vd_break_val"].median())
    hd_max    = float(breakpoints["hd_break_val"].median())
    mrvbf_min = float(breakpoints["mrvbf_break_val"].median())

    print(f"Thresholds derived from {len(breakpoints)} cross-sections:")
    print(f"  vd_max    = {vd_max:.2f} m")
    print(f"  hd_max    = {hd_max:.2f} m")
    print(f"  mrvbf_min = {mrvbf_min:.3f}")

    return {
        "vd_max"      : vd_max,
        "hd_max"      : hd_max,
        "mrvbf_min"   : mrvbf_min,
        "breakpoints" : breakpoints,
    }


def compute_floodplain_probability(vd_path, hd_path, mrvbf_path, thresholds,
                                    out_path):
    """
    Combine VD, HD and MRVBF into a floodplain probability map using
    fuzzy membership functions.

    Equivalent to Step 4 in the R floodplain delineation script.

    Fuzzy membership functions:
    - VD:    decreasing (high VD = far above channel = low probability)
    - HD:    decreasing (high HD = far from channel = low probability)
    - MRVBF: increasing (high MRVBF = flat valley = high probability)

    Final probability = mean of three fuzzy layers (0-1).

    Parameters:
    -----------
    vd_path    : str  - path to Vertical Distance raster
    hd_path    : str  - path to Horizontal Distance raster
    mrvbf_path : str  - path to MRVBF raster
    thresholds : dict - output of find_breakpoints()
                        keys: vd_max, hd_max, mrvbf_min
    out_path   : str  - path for output probability GeoTIFF

    Returns:
    --------
    str - path to output floodplain probability raster (0-1)

    Notes:
    ------
    - Fixed lower bounds follow R script: vd_min=0, hd_min=0, mrvbf_max=6
    - Values outside [0,1] are clipped by fuzzy functions
    - NoData pixels propagate as NaN in the output
    """
    # Check if output already exists
    if os.path.exists(out_path):
        print(f"Floodplain probability already exists, skipping: {out_path}")
        return out_path

    # Fixed lower/upper bounds from R script
    vd_min    = 0.0
    hd_min    = 0.0
    mrvbf_max = 6.0

    vd_max    = thresholds["vd_max"]
    hd_max    = thresholds["hd_max"]
    mrvbf_min = thresholds["mrvbf_min"]

    def fuzzy_decreasing(x, xmin, xmax):
        """High values --> low membership (VD, HD)."""
        if xmax == xmin:
            return np.zeros_like(x)
        return np.clip((xmax - x) / (xmax - xmin), 0, 1)

    def fuzzy_increasing(x, xmin, xmax):
        """High values --> high membership (MRVBF)."""
        if xmax == xmin:
            return np.zeros_like(x)
        return np.clip((x - xmin) / (xmax - xmin), 0, 1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print("Computing floodplain probability map...")
    with rasterio.open(vd_path) as vd_src, \
         rasterio.open(hd_path) as hd_src, \
         rasterio.open(mrvbf_path) as mrvbf_src:

        meta = vd_src.meta.copy()
        meta.update({"dtype": "float32", "nodata": -9999})

        vd    = vd_src.read(1).astype("float32")
        hd    = hd_src.read(1).astype("float32")
        mrvbf = mrvbf_src.read(1).astype("float32")

        # Mask nodata
        nodata_mask = (
            (vd    == vd_src.nodata)    if vd_src.nodata    else np.zeros_like(vd,    dtype=bool)
        ) | (
            (hd    == hd_src.nodata)    if hd_src.nodata    else np.zeros_like(hd,    dtype=bool)
        ) | (
            (mrvbf == mrvbf_src.nodata) if mrvbf_src.nodata else np.zeros_like(mrvbf, dtype=bool)
        )

        # Compute fuzzy membership
        vd_fuzzy    = fuzzy_decreasing(vd,    vd_min,    vd_max)
        hd_fuzzy    = fuzzy_decreasing(hd,    hd_min,    hd_max)
        mrvbf_fuzzy = fuzzy_increasing(mrvbf, mrvbf_min, mrvbf_max)

        # Combined probability = mean of three layers
        flood_prob = (vd_fuzzy + hd_fuzzy + mrvbf_fuzzy) / 3.0
        flood_prob[nodata_mask] = -9999

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(flood_prob, 1)

    valid = flood_prob[flood_prob != -9999]
    print(f"Floodplain probability map saved: {out_path}")
    print(f"  Range: {valid.min():.3f} – {valid.max():.3f}")
    print(f"  Mean:  {valid.mean():.3f}")

    return out_path
