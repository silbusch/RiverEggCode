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

# Columns that are classified per reach (in display order top -> bottom)
REACH_EGG_COLS = ["egg_SL", "egg_P", "egg_QT", "egg_TM"]


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
    One row per reach, with global_id and RT repeated for each reach.

    Columns:
        global_id, strahler_order, RT, n_reaches,
        reach_position (1=upstream), reach_id, len_m,
        egg_SL, egg_P, egg_QT, egg_TM
    """
    rows = []
    for egg in eggs:
        for pos, reach in enumerate(egg["reaches"], start=1):
            row = {
                "global_id": egg["global_id"],
                "strahler_order": egg["strahler_order"],
                "RT": egg["RT"],
                "n_reaches": egg["n_reaches"],
                "reach_position": pos, # 1 = most upstream
            }
            row.update(reach)
            rows.append(row)

    return pd.DataFrame(rows)


def egg_to_string(egg):
    """
    Format one Egg as a readable string for display or logging.

    Example output:
        ═══════════════════════════════════════
        global_id: 1042  |  strahler: 3  |  n_reaches: 3
        RT: None
        ───────────────────────────────────────
        #   reach_id    len_m   SL   P    QT   TM
        1   r001        4821     3   St    1   Bl
        2   r002        3102     3   St    1   Bl
        3   r003        6440     2   Br    3   Mx
        ═══════════════════════════════════════
    """
    lines = []
    lines.append("═" * 55)
    lines.append(
        f"global_id: {egg['global_id']}  |  "
        f"strahler: {egg['strahler_order']}  |  "
        f"n_reaches: {egg['n_reaches']}"
    )
    lines.append(f"RT: {egg['RT']}")
    lines.append("─" * 55)

    # Header
    lines.append(f"{'#':<4} {'reach_id':<12} {'len_m':<8} "
                 f"{'SL':<5} {'P':<6} {'QT':<5} {'TM':<5}")

    # One row per reach
    for pos, reach in enumerate(egg["reaches"], start=1):
        lines.append(
            f"{pos:<4} "
            f"{str(reach['reach_id']):<12} "
            f"{str(reach['len_m']):<8} "
            f"{str(reach.get('egg_SL', '–')):<5} "
            f"{str(reach.get('egg_P', '–')):<6} "
            f"{str(reach.get('egg_QT','–')):<5} "
            f"{str(reach.get('egg_TM', '–')):<5}"
        )

    lines.append("═" * 55)
    return "\n".join(lines)