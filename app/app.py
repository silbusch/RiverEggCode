# app/app.py
# ============================================================
# RiverEggCode - Streamlit App
# ============================================================

import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
import sys

# ============================================================
# Page configuration
# ============================================================
st.set_page_config(
    page_title="RiverEggCode",
    layout="wide"
)

# ============================================================
# Paths - relative to app.py
# ============================================================
DATA_PROCESSED = os.path.join("..", "data", "processed")

# ============================================================
# Load data
# ============================================================
# cache so data is only loaded once
@st.cache_data  
def load_data(study_area):
    """Load classified SWORD reaches for a given study area."""
    path = os.path.join("data", f"sword_{study_area}_classified.parquet")
    gdf = gpd.read_parquet(path)
    # Reproject to WGS84 for Folium
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

# ============================================================
# Sidebar - controls
# ============================================================
st.sidebar.title("RiverEggCode")
st.sidebar.markdown("-")

# Study area selector
study_area = st.sidebar.selectbox(
    "Select river:",
    options=["naryn"],  # NOTE: adding more example rivers later
    index=0
)

# Load data
gdf = load_data(study_area)

# Strahler order filter
strahler_values = sorted(gdf["strahler_order_RiverATLAS"].dropna().unique().tolist())
selected_strahler = st.sidebar.multiselect(
    "Filter by Strahler order:",
    options=strahler_values,
    default=strahler_values  # all selected by default
)

# Apply filter
gdf_filtered = gdf[gdf["strahler_order_RiverATLAS"].isin(selected_strahler)]

# ============================================================
# Main page
# ============================================================
st.title("RiverEggCode")
st.markdown(f"Showing **{len(gdf_filtered)}** reaches for **{study_area.capitalize()}**")

# ============================================================
# Color palette per Strahler order (index 0 = order 1)
# ============================================================
STRAHLER_COLORS = [
    "#3e7d0d", # order 1
    "#2222a6", # order 2
    "#d7ef04", # order 3
    "#00eeff", # order 4
    "#b700e0", # order 5
    "#a50f15", # order 6+
]

# ============================================================
# Map
# ============================================================
# center = [gdf_filtered.geometry.centroid.y.mean(),
#           gdf_filtered.geometry.centroid.x.mean()]

bounds = gdf_filtered.total_bounds  # [minx, miny, maxx, maxy]
center = [(bounds[1] + bounds[3]) / 2,  # lat
          (bounds[0] + bounds[2]) / 2]  # lon

m = folium.Map(location=center, zoom_start=8,
               tiles="CartoDB positron")

for _, row in gdf_filtered.iterrows():
    strahler = row.get("strahler_order_RiverATLAS", 1)
    color = STRAHLER_COLORS[min(int(strahler or 1) - 1, len(STRAHLER_COLORS) - 1)]

    popup_html = f"""
    <b>Reach:</b> {row['reach_id']}<br>
    <b>River:</b> {row.get('river_name', '-')}<br>
    <b>Strahler:</b> {strahler}<br>
    <hr>
    <b>Egg Code:</b><br>
    SL: {row.get('egg_SL', '-')} | 
    P: {row.get('egg_P', '-')} | 
    QT: {row.get('egg_QT', '-')} | 
    TM: {row.get('egg_TM', '-')}
    """

    folium.GeoJson(
        row.geometry,
        style_function=lambda x, c=color: {
            "color": c,
            "weight": 3,
            "opacity": 0.8
        },
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Reach {row['reach_id']} | Strahler {strahler}"
    ).add_to(m)

st_folium(m, width=None, height=600)