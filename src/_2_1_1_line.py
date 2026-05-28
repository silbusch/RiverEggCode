# src/_2_1_1_line.py
# ============================================================
# 2.1.1 LINE JOIN - GRIT strahler order to SWORD reaches
#
# Problem with sjoin_nearest:
#   Only compares the single closest point between geometries.
#   A long reach running mostly beside Strahler 3 but touching
#   Strahler 4 at its tip gets wrongly assigned to Strahler 4.
#
# Solution: sample points along each SWORD reach, assign each
#   point to nearest GRIT feature, majority vote decides.
# ============================================================

import numpy as np
import geopandas as gpd
import pandas as pd
import networkx as nx


def majority_vote(series):
    """Return most frequent value. Ties go to lower value."""
    return series.value_counts().idxmax()


def join_line_majority(sword, grit,
                       cols_to_join,
                       rename_cols,
                       max_distance_m=100,
                       sample_distance_m=50,
                       crs_meters="EPSG:32643",
                       prefix="default"):
    """
    Join attributes from a line GeoDataFrame (e.g. GRIT) to SWORD reaches
    using majority-vote sampling along each reach, meaning that points along the line
    are sampeld to the reaches and via majority-vote the strahler is choosen.

    Parameters:
    -----------
    sword: GeoDataFrame - SWORD reaches
    grit: GeoDataFrame - line dataset to join from
    cols_to_join: list of str - columns to transfer from grit
    rename_cols: dict- {original_name: new_name}
    max_distance_m: float - max distance for sjoin_nearest (meters)
    sample_distance_m: float - sample one point every N meters
    crs_meters: str - projected CRS for distance calculations
    prefix: str - prefix for joined columns 

    Returns:
    --------
    GeoDataFrame: SWORD with new columns added
    """
    # Reproject both to metric CRS
    sword_m = sword.to_crs(crs_meters)
    grit_m  = grit.to_crs(crs_meters)

    # sample points along each SWORD reach
    reach_lengths = sword_m.geometry.length
    n_samples = (reach_lengths / sample_distance_m).astype(int).clip(lower=1)

    reach_indices = np.repeat(sword_m.index.values, n_samples.values)
    distances = np.concatenate([
        np.linspace(0, length, n)
        for length, n in zip(reach_lengths.values, n_samples.values)
    ])

    reach_geoms_repeated = sword_m.geometry.loc[reach_indices]
    sample_points = reach_geoms_repeated.interpolate(distances)

    samples = gpd.GeoDataFrame(
        {"sword_index": reach_indices},
        geometry=sample_points.values,
        crs=crs_meters
    )

    print(f"SWORD reaches: {len(sword_m)}")
    print(f"Sample points: {len(samples)}")
    print(f"Avg pts/reach: {len(samples)/len(sword_m):.1f}")

    #Assign each point to nearest GRIT feature
    join_cols = [c for c in cols_to_join if c != "geometry"] + ["geometry"]
    points_joined = gpd.sjoin_nearest(
        samples,
        grit_m[join_cols],
        how="left",
        max_distance = max_distance_m,
        distance_col="_dist_to_grit"
    )

    # Majority vote per SWORD reach
    primary_col = [c for c in cols_to_join if c != "geometry"][0]

    majority = (points_joined
        .dropna(subset=[primary_col])
        .groupby("sword_index")[primary_col]
        .agg(majority_vote)
        .rename(f"{primary_col}_majority"))

    # also carry over secondary columns (e.g. global_id)
    secondary_cols = [c for c in cols_to_join if c not in ("geometry", primary_col)]
    majority_secondary = {}
    for sec_col in secondary_cols:
        majority_secondary[sec_col] = (points_joined
            .dropna(subset=[primary_col])
            .groupby("sword_index")
            .apply(lambda df: df.loc[
                df[primary_col] == majority_vote(df[primary_col]),
                sec_col
            ].iloc[0])
            .rename(f"{sec_col}_majority"))

    # Confidence score (fraction of points agreeing)
    confidence = (points_joined
        .dropna(subset=[primary_col])
        .groupby("sword_index")
        .apply(lambda df: (
            df[primary_col] == majority_vote(df[primary_col])
        ).mean())
        .rename(f"{prefix}_majority_confidence"))

    #Join all back to SWORD
    result = sword.join(majority)
    for sec_series in majority_secondary.values():
        result = result.join(sec_series)
    result = result.join(confidence)

    # {prefix}_matched: True if at least one sample point found a feature within max_distance_m
    result[f"{prefix}_matched"] = result[f"{prefix}_majority_confidence"].notna()

    # {prefix}_ambiguous: True if matched but less than 60% of sample points agreed
    # NOTE: unmatched reaches ({prefix}_matched=False) are NOT flagged as ambiguous
    result[f"{prefix}_ambiguous"] = (
        result[f"{prefix}_matched"] &
        (result[f"{prefix}_majority_confidence"] < 0.6)
    )

    # Rename columns
    rename_map = {
        f"{primary_col}_majority": rename_cols.get(primary_col, primary_col)
    }
    for sec_col in secondary_cols:
        rename_map[f"{sec_col}_majority"] = rename_cols.get(sec_col, sec_col)
    result = result.rename(columns=rename_map)

    # Drop auto generated sjoin index
    result = result.drop(columns=["index_right"], errors="ignore")

    # Quality report
    joined_col = rename_cols.get(primary_col, primary_col)
    n_matched   = result[joined_col].notna().sum()
    n_unmatched = result[joined_col].isna().sum()
    print(f"\nResults:")
    print(f"  Matched   : {n_matched} / {len(sword)}")
    print(f"  Unmatched : {n_unmatched}")
    print(f"  Confidence distribution:")
    print(f"  {result[f'{prefix}_majority_confidence'].describe().round(3)}")

    return result


def compute_strahler_segments(river_atlas_gdf, hyriv_col="HYRIV_ID", 
                               next_down_col="NEXT_DOWN",
                               strahler_col="ORD_STRA"):
    """
    Compute spatially connected segments of equal Strahler order
    using NEXT_DOWN topology from RiverATLAS.
    
    Reaches with the same Strahler order that are directly connected
    (via NEXT_DOWN) are assigned the same segment_id. This prevents
    spatially distant reaches of equal order from being grouped together.

    Parameters:
    -----------
    river_atlas_gdf : GeoDataFrame - RiverATLAS reaches with NEXT_DOWN
    hyriv_col : str - column with unique reach ID
    next_down_col : str - column with downstream reach ID
    strahler_col : str - column with Strahler order

    Returns:
    --------
    GeoDataFrame : input with new column 'strahler_segment_id' added
    """
    result = river_atlas_gdf.copy()
    
    # Build set of valid HYRIV_IDs for fast lookup
    valid_ids = set(result[hyriv_col].values)

    # Build directed graph, only connect reaches of same Strahler order
    G = nx.DiGraph()
    for _, row in result.iterrows():
        hyriv    = row[hyriv_col]
        next_down = row[next_down_col]
        ord_stra  = row[strahler_col]
        G.add_node(hyriv, ord_stra=ord_stra)

        # Only add edge if downstream reach exists AND has same Strahler order
        if next_down in valid_ids:
            next_ord = result.loc[result[hyriv_col] == next_down, strahler_col].values
            if len(next_ord) > 0 and next_ord[0] == ord_stra:
                G.add_edge(hyriv, next_down)

    # Find weakly connected components, these are the segments
    components = list(nx.weakly_connected_components(G))

    # Assign a unique segment_id to each component
    hyriv_to_segment = {}
    for seg_id, component in enumerate(components):
        for hyriv in component:
            hyriv_to_segment[hyriv] = seg_id

    result["strahler_segment_id"] = result[hyriv_col].map(hyriv_to_segment)

    print(f"RiverATLAS reaches: {len(result)}")
    print(f"Strahler segments found: {result['strahler_segment_id'].nunique()}")
    print(f"Avg reaches per segment: {len(result) / result['strahler_segment_id'].nunique():.1f}")

    return result