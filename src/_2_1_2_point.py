# src/_2_1_2_point.py
# ============================================================
# 2.1.2 POINT SNAP: snap point features to SWORD reach lines
#
# Snaps point features (e.g. dams, gauges) to the nearest
# SWORD reach line. Returns snapped points with reach_id.
#
# References:
#   Ward, B. (2019): "How to leverage Geopandas for faster snapping of points to lines". 
#       URL: https://medium.com/@brendan_ward/how-to-leverage-geopandas-for-faster-snapping-of-points-to-lines-6113c94e59aa
#
#   Lehner, B. et al.(2024): Global Dam Watch database version 1.0. 
#       URL: https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293

#   https://www.globaldamwatch.org/database

# ============================================================

import numpy as np
import geopandas as gpd
import pandas as pd

def snap_points_to_lines(points, lines,
                         tolerance_m=164, # estimated by statistics for Naryn_SWORD und Naryn_GDW
                         crs_meters="EPSG:32643",
                         line_id_col="reach_id"):
    """
    Snap point features to nearest line feature within tolerance.

    Parameters:
    -----------
    points       : GeoDataFrame - point features to snap (e.g. GDW dams)
    lines        : GeoDataFrame - line features to snap to (SWORD reaches)
    tolerance_m  : float- max snap distance in meters
    crs_meters   : str - projected CRS for distance calculations
    line_id_col  : str - column in lines to carry over (e.g. reach_id)

    Returns:
    --------
    GeoDataFrame: snapped points with geometry updated and line_id added
    """
    # Reproject to metric CRS
    pts = points.to_crs(crs_meters).copy()
    lns = lines.to_crs(crs_meters).copy()

    # Build spatial index on lines
    lns.sindex

    # Create bounding boxes around each point
    offset = tolerance_m
    pts_bbox = pts.bounds + [-offset, -offset, offset, offset]

    # Find candidate lines for each point
    hits = pts_bbox.apply(
        lambda row: list(lns.sindex.intersection(row)), axis=1
    )

    # Check for unmatched points
    has_match = hits.apply(len) > 0
    n_no_match = (~has_match).sum()
    if n_no_match > 0:
        print(f"Points with no nearby line: {n_no_match} (outside tolerance)")

    # Build long DataFrame: one row per (point, candidate line) pair
    tmp = pd.DataFrame({
        "pt_idx": np.repeat(hits.index, hits.apply(len)),
        "line_i": np.concatenate(hits.values)
    })

    tmp = tmp.join(lns.reset_index(drop=True), on="line_i")
    tmp = tmp.join(pts.geometry.rename("point"), on="pt_idx")
    tmp = gpd.GeoDataFrame(tmp, geometry="geometry", crs=crs_meters)

    # Compute distance from each point to each candidate line
    tmp["snap_dist"] = tmp.geometry.distance(gpd.GeoSeries(tmp.point))

    # Filter by tolerance
    tmp = tmp.loc[tmp["snap_dist"] <= tolerance_m]

    # Keep only the closest line per point
    tmp = tmp.sort_values("snap_dist")
    closest = tmp.groupby("pt_idx").first()
    closest = gpd.GeoDataFrame(closest, geometry="geometry", crs = crs_meters)

    # Snap point to exact position on nearest line
    pos = closest.geometry.project(gpd.GeoSeries(closest.point))
    snapped_geom = closest.geometry.interpolate(pos)

    line_cols = ["line_i", line_id_col, "snap_dist"]
    line_cols = [c for c in line_cols if c in closest.columns]

    snapped = gpd.GeoDataFrame(
        closest[line_cols],
        geometry=snapped_geom,
        crs=crs_meters
    )

    # Join back to original points
    result = points.drop(columns=["geometry"]).join(snapped)
    result = result.dropna(subset=["geometry"])
    result = gpd.GeoDataFrame(result, geometry="geometry", crs=crs_meters)
    result = result.to_crs(points.crs)

    print(f"Points input: {len(points)}")
    print(f"Points snapped: {len(result)}")
    print(f"Snap distance (m):")
    print(f"{result['snap_dist'].describe().round(1)}")

    return result