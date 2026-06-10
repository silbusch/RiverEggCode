# src/_3_2_2_egg_code.py

# ============================================================
# EGG CODE BUILDER
# Aggregates classified SWORD reaches into one Egg per global_id of GRITv1.0.
# Reaches are ordered from upstream to downstream (dist_out desc).
#
# Egg structure per global_id:
#   NOTE: RT – River type (placeholder, filled later)
#   Per reach (upstream → downstream):
#   reach_id, len_m, egg_SL, egg_P, egg_QT, egg_TM
# ============================================================

import pandas as pd
import numpy as np

from _3_2_1_classifier import DEFAULT_CLASSIFIERS

# Columns that are classified per reach (in display order top -> bottom)
REACH_EGG_COLS = [c.name for c in DEFAULT_CLASSIFIERS if c.available]



def build_egg(group, grouped_col, strahler_col):
    """
    Build one Egg dictionary from a group of SWORD reaches
    sharing the same grouped_col.

    Reaches are sorted upstream → downstream via dist_out (descending).
    dist_out = distance to outlet → higher value = further upstream.

    Returns: dict with Egg structure
    """
    # Sort reaches upstream → downstream
    group = group.sort_values("dist_out", ascending=False)

    # Build the per-reach data (the "columns" of the Egg)
    reaches = []
    for _, row in group.iterrows():
        reach_entry = {
            "reach_id" : row["reach_id"],
            "len_m" : int(round(row["reach_len"])) if pd.notna(row.get("reach_len")) else None,
        }
        for col in REACH_EGG_COLS:
            reach_entry[col] = row[col] if col in row.index else None
        reaches.append(reach_entry)

    # Build the full Egg
    egg = {
        "global_id": group[grouped_col].iloc[0],
        "strahler_order": group[strahler_col].iloc[0],
        "n_reaches": len(group),
        #NOTE: River type: placeholder until more data joined
        "RT": None,   
        "reaches": reaches
    }
    return egg



def build_all_eggs(gdf, grouped_col, strahler_col):
    """
    Build one Egg per grouped_col (e.g. global_id_GRITv1.0) from a classified GeoDataFrame.

    Parameters:
    -----------
    gdf: 
    grouped_col: str - 
    strahler_col: str -


    Returns: list of Egg dicts, one per global_id
    """
    eggs = []
    grouped = gdf.groupby(grouped_col, dropna=True)

    for global_id, group in grouped:
        egg = build_egg(group, grouped_col, strahler_col)
        eggs.append(egg)

    print(f"Eggs built: {len(eggs)}")
    print(f"Total reaches covered: {sum(e['n_reaches'] for e in eggs)}")
    return eggs



def egg_to_dataframe(eggs):
    """
    Convert list of Eggs to a flat DataFrame for export to GeoPackage/CSV.
    One row per reach, with global_id and RT (river type) repeated for each reach.

    Columns:
        global_id, strahler_order, RT, n_reaches,
        reach_position (1=upstream), reach_id, len_m,
        egg_SL, egg_P, egg_QT
    """
    rows = []
    for egg in eggs:
        for pos, reach in enumerate(egg["reaches"], start=1):
            row = {
                "global_id"     : egg.get("global_id", None),
                "strahler_order": egg.get("strahler_order", None),
                "RT"            : egg.get("RT", None),
                "n_reaches"     : egg.get("n_reaches", None),
                "reach_position": pos,
            }
            row.update(reach)
            rows.append(row)
    return pd.DataFrame(rows)



def egg_to_string(egg):
    """
    Format one Egg as a readable string for display or logging.
    Works for both grouping approaches (strahler_segment and basin_6).
    """
    lines = []
    lines.append("═" * 65)

    # Egg header, strahler_order optional
    strahler = egg.get("strahler_order", None)
    if strahler is not None:
        lines.append(
            f"global_id: {egg['global_id']}|"
            f"strahler: {strahler}  |  "
            f"n_reaches: {egg['n_reaches']}"
        )
    else:
        lines.append(
            f"global_id: {egg['global_id']}|"
            f"n_reaches: {egg['n_reaches']}"
        )
    lines.append(f"RT: {egg.get('RT', None)}")
    lines.append("-" * 65)

    # Header
    col_labels = [col.replace("egg_", "") for col in REACH_EGG_COLS]

    header = (
    f"{'#':<4} {'reach_id':<12} {'len_m':<8} "
    + " ".join(f"{label:<6}" for label in col_labels)
    + f" {'Strahler':<5}"
    )
    lines.append(header)

    for pos, reach in enumerate(egg["reaches"], start=1):
        egg_values = " ".join(
            f"{str(reach.get(col, '-')):<6}" for col in REACH_EGG_COLS
        )
        lines.append(
            f"{pos:<4} "
            f"{str(reach['reach_id']):<12} "
            f"{str(reach['len_m']):<8} "
            f"{egg_values} "
            f"{str(reach.get('strahler_order', '-')):<5}"
        )

    lines.append("═" * 65)
    return "\n".join(lines)



def extract_basin6(reach_id):
    """
    Extract Pfafstetter Level 6 basin code from SWORD reach_id.
    
    reach_id format: CBBBBBRRRRT
    - C      : Continent (1 digit)
    - BBBBB  : Pfafstetter basin code up to level 6 (5 digits)
    - RRR    : Reach number within basin (3 digits)
    - T      : Type (1 digit)
    
    Returns: str - first 6 digits of reach_id
    """
    return str(reach_id)[:6]



def build_basin6_eggs(gdf, strahler_col="strahler_order_RiverATLAS"):
    """
    Build one Egg per Pfafstetter Level 6 basin using the SWORD reach_id structure.
    All reaches sharing the same first 6 digits of reach_id belong to the same basin.
    Reaches are sorted upstream to downstream via dist_out (descending).

    This approach requires no external dataset, basin membership is encoded
    directly in the SWORD reach_id.

    Parameters:
    -----------
    gdf          : GeoDataFrame - classified SWORD reaches
    strahler_col : str - column with Strahler order (default: strahler_order_RiverATLAS)

    Returns:
    --------
    list of Egg dicts, one per Level 6 basin
    """
    result = gdf.copy()

    # Extract basin_6 from reach_id
    result["basin_6"] = result["reach_id"].astype(str).str[:6]

    eggs = []
    grouped = result.groupby("basin_6", dropna=True)
    
    for basin_id, group in grouped:
        # Sort reaches upstream to downstream
        group = group.sort_values("dist_out", ascending=False)

        # Build per-reach data
        reaches = []
        for _, row in group.iterrows():
            reach_entry = {
                "reach_id"       : row["reach_id"],
                "len_m"          : int(round(row["reach_len"])) if pd.notna(row.get("reach_len")) else None,
                "strahler_order" : row.get("strahler_order_RiverATLAS", None),  # reach-level attribute
            }
            for col in REACH_EGG_COLS:
                reach_entry[col] = row[col] if col in row.index else None
            reaches.append(reach_entry)

        egg = {
            "global_id"     : basin_id,
            "n_reaches"     : len(group),
            "RT"            : None,
            "reaches"       : reaches
        }
        eggs.append(egg)

    print(f"Basin6 Eggs built: {len(eggs)}")
    print(f"Total reaches covered: {sum(e['n_reaches'] for e in eggs)}")
    return eggs