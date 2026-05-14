# src/_2_3_raster_join.py
# ============================================================
# 2.3.1 RASTER TO VECTOR JOIN

# Extracts raster values along SWORD reach lines.
# Buffer is based on SWORD width column + fixed offset.
#
# Buffer logic:
#   buffer = clip((width/2) + offset, min, max)
#   Accounts for SWORD positional uncertainty + real river width
# ============================================================

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import mapping
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(__file__))

from _00_config import (
    RASTER_NODATA_THRESHOLD,
    RASTER_BUFFER_OFFSET_M,
    RASTER_BUFFER_MIN_M,
    RASTER_BUFFER_MAX_M
)


def compute_buffer_radius(gdf, width_col="width"):
    """
    Compute per-reach buffer radius based on SWORD width column.

    buffer = clip((width/2) + offset, min, max)

    Returns: pd.Series of buffer radii in meters
    """
    if width_col not in gdf.columns:
        print(f"Column '{width_col}' not found -> using minimum buffer")
        return pd.Series(RASTER_BUFFER_MIN_M, index=gdf.index)

    buffer = (gdf[width_col] / 2) + RASTER_BUFFER_OFFSET_M
    buffer = buffer.clip(lower=RASTER_BUFFER_MIN_M,
                         upper=RASTER_BUFFER_MAX_M)

    print(f"Buffer radius (m):")
    print(f" min  {buffer.min():.1f}")
    print(f" median: {buffer.median():.1f}")
    print(f" max: {buffer.max():.1f}")

    return buffer


def extract_raster_values(gdf, raster_path, col_name,
                          width_col="width",
                          crs_meters="EPSG:32643"):
    """
    Extract raster values along each SWORD reach.
    Buffer per reach = (width/2) + offset, clipped to [min, max].

    Parameters:
    -----------
    gdf         : GeoDataFrame - SWORD reaches
    raster_path : str - path to .tif raster
    col_name    : str - base name for output columns
                                 -> {col_name}_mean, {col_name}_median
    width_col   : str - SWORD column with river width in meters
    crs_meters  : str - projected CRS for buffering

    Returns:
    --------
    GeoDataFrame with two new columns added:
        {col_name}_mean
        {col_name}_median
    """
    result = gdf.copy()

    # Initialize output columns
    result[f"{col_name}_mean"]   = np.nan
    result[f"{col_name}_median"] = np.nan

    # compute per-reach buffer radii
    print(f"\nComputing buffers for {len(gdf)} reaches...")
    buffer_radii = compute_buffer_radius(gdf, width_col=width_col)

    # reproject to metric CRS and apply per-reach buffer
    gdf_meters   = gdf.to_crs(crs_meters)
    gdf_buffered = gdf_meters.copy()
    gdf_buffered["geometry"] = gdf_meters.geometry.buffer(buffer_radii)
    # geometry is now a polygon (buffered zone around reach line)

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        nodata     = src.nodata if src.nodata is not None \
                     else RASTER_NODATA_THRESHOLD

        print(f"\nRaster CRS: {raster_crs}")
        print(f"Raster shape: {src.width} x {src.height} pixels")
        print(f"Nodata value: {nodata}")

        # Reproject buffered geometries to raster CRS
        gdf_reproj = gdf_buffered.to_crs(raster_crs)

        n_success = 0
        n_empty = 0
        n_outside = 0

        for idx, row in gdf_reproj.iterrows():
            geom = row.geometry

            if geom is None or geom.is_empty:
                n_empty += 1
                continue

            try:
                # Windowed read, only loads pixels within buffer polygon
                pixel_values, _ = rio_mask(
                    src,
                    [mapping(geom)],
                    crop=True, # crop to bounding box of buffer
                    all_touched=True, # include pixels touching buffer edge
                    nodata=nodata
                )

                # Flatten and filter nodata / NaN
                values = pixel_values.flatten().astype(float)
                values = values[values != nodata]
                values = values[~np.isnan(values)]

                if len(values) == 0:
                    n_empty += 1
                    continue

                result.at[idx, f"{col_name}_mean"]   = float(np.mean(values))
                result.at[idx, f"{col_name}_median"] = float(np.median(values))
                n_success += 1

            except Exception:
                # Reach outside raster extent -> NaN
                n_outside += 1
                continue

        print(f"\nResults:")
        print(f"  Matched    : {n_success} / {len(gdf)}")
        print(f"  Empty/NaN  : {n_empty}")
        print(f"  Outside    : {n_outside}")

    return result