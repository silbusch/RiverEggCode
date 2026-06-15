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

def snap_gdw_to_sword_nodes(gdw, 
                          nodes, 
                          instream_only=True,
                          buffer_start_m=500, 
                          buffer_step_m=250, 
                          buffer_max_m=2000,
                          crs_meters="EPSG:32643"):
    """
    Snap GDW dam points to the nearest SWORD node with obstr_type > 0.
    
    Buffer expands in steps from buffer_start_m to buffer_max_m
    until a matching node is found. GDW points with no match within
    buffer_max_m are returned separately as 'unmatched'.

    Parameters:
    -----------
    gdw            : GeoDataFrame - GDW dam points (filtered to INSTREAM=1)
    nodes          : GeoDataFrame - SWORD nodes with obstr_type column
    instream_only : bool - if True, filter GDW to INSTREAM == "Instream" before snapping
    buffer_start_m : float - initial search radius
    buffer_step_m  : float - radius increment per iteration
    buffer_max_m   : float - max search radius before marking unmatched
    crs_meters   : str - projected CRS for distance calculations

    Returns:
    --------
    matched   : GeoDataFrame - GDW points with node_id, snap_dist, n_buffer_steps
    unmatched : GeoDataFrame - GDW points with no SWORD dam node within buffer_max_m
    """
    # Filtering for those GDW points which are located within the river (INSTREAM)
    if instream_only:
        gdw = gdw[gdw["INSTREAM"] == "Instream"].copy()
        print(f"GDW filtered to INSTREAM: {len(gdw)}")

    # Prepare
    # Filtering SWORD nodes to dam nodes only
    dam_nodes = nodes[nodes["obstr_type"] > 0].copy()

    # reproject everything to metric UTM CRS for distance calculation
    gdw_m = gdw.to_crs(crs_meters).copy()
    dam_nodes_m = dam_nodes.to_crs(crs_meters).copy() 
    print(f"GDW points to process: {len(gdw_m)}")
    print(f"SWORD dam nodes available: {len(dam_nodes_m)}")

    # placeholders  
    matched_rows = []
    unmatched_rows = []

    # for each GDW point, search with expanding buffer, if no match with first buffer
    for gdw_idx, gdw_row in gdw_m.iterrows():
        gdw_point = gdw_row.geometry
        found = False
        buffer_radius = buffer_start_m
        n_steps = 0

        while buffer_radius <= buffer_max_m:
            # Distance from this GDW point to all dam nodes
            distances = dam_nodes_m.geometry.distance(gdw_point)

            # Which dam nodes are within the current buffer?
            within_buffer = distances[distances <= buffer_radius]

            if len(within_buffer) > 0:
                # Found at least one and take the closest
                closest_idx = within_buffer.idxmin()
                closest_dist = within_buffer.min()
                closest_node = dam_nodes_m.loc[closest_idx]

                matched_rows.append({
                    "gdw_idx": gdw_idx,
                    "node_id": closest_node["node_id"],
                    "reach_id": closest_node["reach_id"],
                    "snap_dist": closest_dist,
                    "n_buffer_steps": n_steps
                })
                found = True
                break

            # No match yet --> expand buffer
            buffer_radius += buffer_step_m
            n_steps += 1

        if not found:
            unmatched_rows.append({
                "gdw_idx": gdw_idx,
                "reason": f"no dam node within {buffer_max_m}m"
            })
        
    # Converting matched results to DataFrame and join back to original GDW attributes
    matched_df = pd.DataFrame(matched_rows)
    
    if len(matched_df) > 0:
        # Join GDW attributes (DAM_NAME, DAM_HGT_M, etc.) using gdw_idx
        matched = gdw.loc[matched_df["gdw_idx"]].reset_index(drop=True)
        matched = pd.concat([matched, matched_df.drop(columns=["gdw_idx"]).reset_index(drop=True)], axis=1)
    else:
        matched = gpd.GeoDataFrame()

    # same for unmatched
    unmatched_df = pd.DataFrame(unmatched_rows)
    
    if len(unmatched_df) > 0:
        unmatched = gdw.loc[unmatched_df["gdw_idx"]].reset_index(drop=True)
        unmatched = pd.concat([unmatched, unmatched_df.drop(columns=["gdw_idx"]).reset_index(drop=True)], axis=1)
    else:
        unmatched = gpd.GeoDataFrame()

    # print summary
    print(f"\nResults:")
    print(f"Matched: {len(matched)} / {len(gdw)}")
    print(f"Unmatched: {len(unmatched)} / {len(gdw)}")
    if len(matched) > 0:
        print(f"Buffer steps needed:")
        print(f"{matched['n_buffer_steps'].value_counts().sort_index()}")

    return matched, unmatched

    




# def snap_points_to_lines(points, lines,
#                          tolerance_m=164, # estimated by statistics for Naryn_SWORD und Naryn_GDW
#                          crs_meters="EPSG:32643",
#                          line_id_col="reach_id"):
#     """
#     Snap point features to nearest line feature within tolerance.

#     Parameters:
#     -----------
#     points       : GeoDataFrame - point features to snap (e.g. GDW dams)
#     lines        : GeoDataFrame - line features to snap to (SWORD reaches)
#     tolerance_m  : float- max snap distance in meters
#     crs_meters   : str - projected CRS for distance calculations
#     line_id_col  : str - column in lines to carry over (e.g. reach_id)

#     Returns:
#     --------
#     GeoDataFrame: snapped points with geometry updated and line_id added
#     """
#     # Reproject to metric CRS
#     pts = points.to_crs(crs_meters).copy()
#     lns = lines.to_crs(crs_meters).copy()

#     # Build spatial index on lines
#     lns.sindex

#     # Create bounding boxes around each point
#     offset = tolerance_m
#     pts_bbox = pts.bounds + [-offset, -offset, offset, offset]

#     # Find candidate lines for each point
#     hits = pts_bbox.apply(
#         lambda row: list(lns.sindex.intersection(row)), axis=1
#     )

#     # Check for unmatched points
#     has_match = hits.apply(len) > 0
#     n_no_match = (~has_match).sum()
#     if n_no_match > 0:
#         print(f"Points with no nearby line: {n_no_match} (outside tolerance)")

#     # Build long DataFrame: one row per (point, candidate line) pair
#     tmp = pd.DataFrame({
#         "pt_idx": np.repeat(hits.index, hits.apply(len)),
#         "line_i": np.concatenate(hits.values)
#     })

#     tmp = tmp.join(lns.reset_index(drop=True), on="line_i")
#     tmp = tmp.join(pts.geometry.rename("point"), on="pt_idx")
#     tmp = gpd.GeoDataFrame(tmp, geometry="geometry", crs=crs_meters)

#     # Compute distance from each point to each candidate line
#     tmp["snap_dist"] = tmp.geometry.distance(gpd.GeoSeries(tmp.point))

#     # Filter by tolerance
#     tmp = tmp.loc[tmp["snap_dist"] <= tolerance_m]

#     # Keep only the closest line per point
#     tmp = tmp.sort_values("snap_dist")
#     closest = tmp.groupby("pt_idx").first()
#     closest = gpd.GeoDataFrame(closest, geometry="geometry", crs = crs_meters)

#     # Snap point to exact position on nearest line
#     pos = closest.geometry.project(gpd.GeoSeries(closest.point))
#     snapped_geom = closest.geometry.interpolate(pos)

#     line_cols = ["line_i", line_id_col, "snap_dist"]
#     line_cols = [c for c in line_cols if c in closest.columns]

#     snapped = gpd.GeoDataFrame(
#         closest[line_cols],
#         geometry=snapped_geom,
#         crs=crs_meters
#     )

#     # Join back to original points
#     result = points.drop(columns=["geometry"]).join(snapped)
#     result = result.dropna(subset=["geometry"])
#     result = gpd.GeoDataFrame(result, geometry="geometry", crs=crs_meters)
#     result = result.to_crs(points.crs)

#     print(f"Points input: {len(points)}")
#     print(f"Points snapped: {len(result)}")
#     print(f"Snap distance (m):")
#     print(f"{result['snap_dist'].describe().round(1)}")

#     return result