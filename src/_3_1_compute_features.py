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