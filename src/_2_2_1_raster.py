# src/_2_2_1_raster.py
# ============================================================
# 2.3.1 RASTER TO VECTOR JOIN

# Extracts raster values along SWORD reach lines.
# Buffer is based on SWORD width column (width of the reach) + fixed offset e.g. 50m.
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
import subprocess
from rasterio.features import rasterize as rio_rasterize
from rasterio.transform import from_bounds
from shapely.geometry import LineString, Point




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
    Suitable for continuous rasters (e.g. mean, median, etc).

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
    result[f"{col_name}_mean"] = np.nan
    result[f"{col_name}_median"] = np.nan

    # compute per-reach buffer radii
    buffer_radii = compute_buffer_radius(gdf, width_col=width_col)

    # reproject to metric CRS and apply per-reach buffer
    gdf_meters = gdf.to_crs(crs_meters)
    gdf_buffered = gdf_meters.copy()
    gdf_buffered["geometry"] = gdf_meters.geometry.buffer(buffer_radii)
    # geometry is now a polygon (buffered zone around reach line)

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        nodata = src.nodata if src.nodata is not None \
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
                    # NOTE: Maybe calculating the area with shapely and 
                    # including only pixel with area of 50%, but too much compute time
                    all_touched=False, # including only pixels whose center lies within the buffer
                    nodata=nodata
                )

                # Flatten and filter nodata/NaN
                values = pixel_values.flatten().astype(float)
                values = values[values != nodata]
                values = values[~np.isnan(values)]

                if len(values) == 0:
                    n_empty += 1
                    continue

                result.at[idx, f"{col_name}_mean"] = float(np.mean(values))
                result.at[idx, f"{col_name}_median"] = float(np.median(values))
                n_success += 1

            except Exception:
                # Reach outside raster extent -> NaN
                n_outside += 1
                continue

        print(f"\nResults:")
        print(f"Matched: {n_success} / {len(gdf)}")
        print(f"Empty/NaN: {n_empty}")
        print(f"Outside: {n_outside}")

    return result


def extract_raster_majority(gdf, raster_path, col_name,
                          width_col="width", crs_meters="EPSG:32643"):
    """
    Extract the majority (most frequent) pixel class along each SWORD reach buffer.
    Suitable for categorical rasters (e.g. land cover, geology classes).

    Parameters:
    -----------
    gdf         : GeoDataFrame - SWORD reaches
    raster_path : str - path to .tif raster
    col_name    : str - base name for output columns
                    -> {col_name}_majority (most frequent pixel class)
                    -> {col_name}_majority_confidence (fraction of pixels agreeing)
    width_col   : str - SWORD column with river width in meters
    crs_meters  : str - projected CRS for buffering

    Returns:
    --------
    GeoDataFrame with two new columns added:
        {col_name}_majority
        {col_name}_majority_confidence
    """
    result = gdf.copy()

    # Initialize output columns
    result[f"{col_name}_majority"] = np.nan
    result[f"{col_name}_majority_confidence"] = np.nan

    # compute per-reach buffer radii
    buffer_radii = compute_buffer_radius(gdf, width_col=width_col)

    # reproject to metric CRS and apply per-reach buffer
    gdf_meters = gdf.to_crs(crs_meters)
    gdf_buffered = gdf_meters.copy()
    gdf_buffered["geometry"] = gdf_meters.geometry.buffer(buffer_radii)
    # geometry is now a polygon (buffered zone around reach line)

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        nodata = src.nodata if src.nodata is not None \
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
                    # NOTE: Maybe calculating the area with shapely and 
                    # including only pixel with area of 50%, but too much compute time
                    all_touched=False, # including only pixels whose center lies within the buffer
                    nodata=nodata
                )

                # Flatten and filter nodata/NaN
                values = pixel_values.flatten().astype(float)
                values = values[values != nodata]
                values = values[~np.isnan(values)]

                if len(values) == 0:
                    n_empty += 1
                    continue

                counts   = np.bincount(values.astype(int))
                majority = int(np.argmax(counts))
                confidence = (values == majority).sum() / len(values)

                result.at[idx, f"{col_name}_majority"]            = majority
                result.at[idx, f"{col_name}_majority_confidence"] = confidence
                n_success += 1

            except Exception:
                # Reach outside raster extent -> NaN
                n_outside += 1
                continue

        print(f"\nResults:")
        print(f"Matched: {n_success} / {len(gdf)}")
        print(f"Empty/NaN: {n_empty}")
        print(f"Outside: {n_outside}")

    return result


def reproject_dem_to_utm(dem_path, out_path, crs_meters="EPSG:32643"):
    """
    Reproject DEM from geographic (EPSG:4326) to metric CRS (UTM).
    Required before SAGA processing – SAGA morphometry tools expect
    metric coordinates for correct gradient and distance calculations.
    
    Parameters:
    -----------
    dem_path   : str - input DEM in EPSG:4326
    out_path   : str - output DEM in metric CRS
    crs_meters : str - target CRS (default: EPSG:32643 for Naryn/Central Asia)
    
    Returns:
    --------
    str - path to reprojected DEM
    """
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    import os

    if os.path.exists(out_path):
        print(f"Reprojected DEM already exists, skipping: {out_path}")
        return out_path

    print(f"Reprojecting DEM to {crs_meters}...")
    with rasterio.open(dem_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, crs_meters, src.width, src.height, *src.bounds
        )
        meta = src.meta.copy()
        meta.update({
            "crs"      : crs_meters,
            "transform": transform,
            "width"    : width,
            "height"   : height,
            "dtype"    : "float32",
            "nodata"   : -9999
        })

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with rasterio.open(out_path, "w", **meta) as dst:
            reproject(
                source      = rasterio.band(src, 1),
                destination = rasterio.band(dst, 1),
                src_transform = src.transform,
                src_crs       = src.crs,
                dst_transform = transform,
                dst_crs       = crs_meters,
                resampling    = Resampling.bilinear
            )

    print(f"Reprojected DEM saved: {out_path}")
    return out_path

# ============================================================
#
# Using SAGA to calculate floodplain width, based on Mariams R-Code
#
# ============================================================
def _tif_to_sgrd(tif_path, saga_cmd, saga_env):
    """
    Convert GeoTIFF to SAGA Grid format (.sgrd) using SAGA io_gdal tool.
    Required because SAGA morphometry tools only accept SAGA Grid as input.
    Returns path to .sgrd file.
    """
    import subprocess
    sgrd_path = tif_path.replace(".tif", ".sgrd")
    if os.path.exists(sgrd_path):
        return sgrd_path
    cmd = [saga_cmd, "io_gdal", "0",
           "-FILES", tif_path,
           "-GRIDS", sgrd_path]
    subprocess.run(cmd, capture_output=True, env=saga_env)
    return sgrd_path


def _sgrd_to_tif(sgrd_path, tif_path, saga_cmd, saga_env):
    """
    Convert SAGA Grid (.sgrd) back to GeoTIFF using SAGA io_gdal tool.
    """
    import subprocess
    cmd = [saga_cmd, "io_gdal", "2",
           "-GRIDS", sgrd_path,
           "-FILE",  tif_path]
    subprocess.run(cmd, capture_output=True, env=saga_env)
    return tif_path

def rasterize_sword(sword_gdf, dem_path, out_path):
    """
    Rasterize SWORD river reaches onto the DEM grid.
    
    Creates a binary raster where pixels intersecting SWORD reaches
    are set to 1 and all other pixels are NoData. This raster serves
    as the channel network input for SAGA's Vertical Distance and
    Horizontal Distance tools.
    
    Parameters:
    -----------
    sword_gdf : GeoDataFrame - SWORD reaches (line geometries)
    dem_path  : str          - path to reference DEM GeoTIFF
                               (defines output resolution, extent, CRS)
    out_path  : str          - path for output raster GeoTIFF

    Returns:
    --------
    str - path to output raster

    Notes:
    ------
    - SWORD reaches are reprojected to match the DEM CRS before rasterizing
    - all_touched=True ensures thin lines are captured at 30m resolution
    - Output dtype is uint8 (1=river, 0=background)
    - Equivalent to R: rasterize(gang_utm, dem, field=1)
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with rasterio.open(dem_path) as dem_src:
        dem_crs       = dem_src.crs
        dem_transform = dem_src.transform
        dem_shape     = (dem_src.height, dem_src.width)
        dem_meta      = dem_src.meta.copy()

    # Reproject SWORD to match DEM CRS
    sword_reproj = sword_gdf.to_crs(dem_crs)

    # Rasterize: burn value 1 where SWORD reaches intersect pixels
    river_raster = rio_rasterize(
        [(geom, 1) for geom in sword_reproj.geometry],
        out_shape   = dem_shape,
        transform   = dem_transform,
        fill        = 0,           # background value
        all_touched = True,        # capture thin lines at 30m resolution
        dtype       = np.uint8
    )

    # Save as GeoTIFF
    dem_meta.update({
        "dtype"  : "float32",  # ← float statt uint8
        "count"  : 1,
        "nodata" : -9999       # ← expliziter NoData Wert
    })

    river_raster = river_raster.astype("float32")
    river_raster[river_raster == 0] = -9999

    with rasterio.open(out_path, "w", **dem_meta) as dst:
        dst.write(river_raster, 1)

    n_river_pixels = int(river_raster.sum())
    print(f"SWORD rasterized: {n_river_pixels} river pixels")
    print(f"Saved: {out_path}")
    return out_path


def compute_mrvbf(dem_path, out_dir, saga_cmd, saga_env,
                  t_slope=16.0, t_pctl_v=0.4, t_pctl_r=0.35):
    """
    Compute Multiresolution Index of Valley Bottom Flatness (MRVBF)
    from a DEM using SAGA GIS (tool ta_morphometry 8).

    MRVBF identifies valley bottoms at multiple scales:
        < 0.5  : erosional terrain (hillslopes, ridges)
        0.5-1.5: steep, narrow valley bottoms
        > 1.5  : flat, wide valley bottoms (floodplains)

    Gallant & Dowling (2003): A multiresolution index of valley bottom
    flatness for mapping depositional areas. WRR 39/12:1347-1359.

    Parameters:
    -----------
    dem_path  : str   - path to input DEM GeoTIFF (e.g. COP30)
    out_dir   : str   - directory for output files
    saga_cmd  : str   - path to saga_cmd.exe
    saga_env  : dict  - environment variables for subprocess (from _0_config_paths)
    t_slope   : float - initial slope threshold (default 16% = SAGA default)
    t_pctl_v  : float - threshold for elevation percentile lowness (default 0.4)
    t_pctl_r  : float - threshold for elevation percentile upness (default 0.35)

    Returns:
    --------
    str - path to output MRVBF GeoTIFF

    Notes:
    ------
    - Default thresholds follow Gallant & Dowling (2003) and are suitable
      for 30m DEMs. For higher resolution DEMs, t_slope may need adjustment.
    - MRVBF is globally applicable without regional calibration.
    - Requires SAGA GIS v7.x accessible via saga_cmd.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_mrvbf = os.path.join(out_dir, "mrvbf.tif")

    if os.path.exists(out_mrvbf):
        print(f"MRVBF already exists, skipping: {out_mrvbf}")
        return out_mrvbf

    # Convert DEM to SAGA Grid
    dem_sgrd     = _tif_to_sgrd(dem_path, saga_cmd, saga_env)
    out_mrvbf_sg = out_mrvbf.replace(".tif", ".sgrd")

    cmd = [
        saga_cmd, "ta_morphometry", "8",
        "-DEM",      dem_sgrd,
        "-MRVBF",    out_mrvbf_sg,
        "-T_SLOPE",  str(t_slope),
        "-T_PCTL_V", str(t_pctl_v),
        "-T_PCTL_R", str(t_pctl_r),
    ]

    print("Computing MRVBF...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=saga_env)

    if result.returncode != 0:
        print(f"SAGA error: {result.stderr[:500]}")
        return None

    _sgrd_to_tif(out_mrvbf_sg, out_mrvbf, saga_cmd, saga_env)
    print(f"MRVBF saved: {out_mrvbf}")
    return out_mrvbf


def compute_vertical_distance(dem_path, river_rast_path, out_dir,
                               saga_cmd, saga_env):
    """
    Compute Vertical Distance to Channel Network using SAGA GIS (ta_channels 3).
    Both DEM and river raster are converted to SAGA Grid format before processing.
    """
    import subprocess
    import os

    os.makedirs(out_dir, exist_ok=True)
    out_vd = os.path.join(out_dir, "vertical_distance.tif")

    if os.path.exists(out_vd):
        print(f"Vertical distance already exists, skipping: {out_vd}")
        return out_vd

    # Convert inputs to SAGA Grid
    dem_sgrd   = _tif_to_sgrd(dem_path,        saga_cmd, saga_env)
    river_sgrd = _tif_to_sgrd(river_rast_path, saga_cmd, saga_env)
    out_vd_sg  = out_vd.replace(".tif", ".sgrd")

    cmd = [
        saga_cmd, "ta_channels", "3",
        "-ELEVATION", dem_sgrd,
        "-CHANNELS",  river_sgrd,
        "-DISTANCE",  out_vd_sg,
    ]

    print("Computing Vertical Distance to Channel Network...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=saga_env)

    if result.returncode != 0:
        print(f"SAGA error: {result.stderr[:500]}")
        return None

    _sgrd_to_tif(out_vd_sg, out_vd, saga_cmd, saga_env)
    print(f"Vertical distance saved: {out_vd}")
    return out_vd


def compute_horizontal_distance(river_rast_path, out_dir,
                                 saga_cmd, saga_env):
    """
    Compute Horizontal Distance (proximity grid) using SAGA GIS (grid_tools 10).
    River raster is converted to SAGA Grid format before processing.
    """
    import subprocess
    import os

    os.makedirs(out_dir, exist_ok=True)
    out_hd = os.path.join(out_dir, "horizontal_distance.tif")

    if os.path.exists(out_hd):
        print(f"Horizontal distance already exists, skipping: {out_hd}")
        return out_hd

    # Convert river raster to SAGA Grid
    river_sgrd = _tif_to_sgrd(river_rast_path, saga_cmd, saga_env)
    out_hd_sg  = out_hd.replace(".tif", ".sgrd")

    cmd = [
        saga_cmd, "grid_tools", "10",
        "-SOURCE",   river_sgrd,
        "-DISTANCE", out_hd_sg,
    ]

    print("Computing Horizontal Distance to Channel Network...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=saga_env)

    if result.returncode != 0:
        print(f"SAGA error: {result.stderr[:500]}")
        return None

    _sgrd_to_tif(out_hd_sg, out_hd, saga_cmd, saga_env)
    print(f"Horizontal distance saved: {out_hd}")
    return out_hd

def clip_dem_to_aoi(dem_path, aoi_gdf, out_path, buffer_m=5000):
    """
    Clip DEM to AOI extent with a buffer.
    
    Reduces SAGA processing area and avoids large VD values from
    distant mountains far outside the study area.
    
    Parameters:
    -----------
    dem_path : str          - path to input DEM GeoTIFF
    aoi_gdf  : GeoDataFrame - AOI polygon (e.g. HydroBASINS Level 5)
    out_path : str          - path for clipped output DEM
    buffer_m : float        - buffer around AOI in meters (default 5000m)

    Returns:
    --------
    str - path to clipped DEM GeoTIFF
    """
    import rasterio
    from rasterio.mask import mask
    import os

    if os.path.exists(out_path):
        print(f"Clipped DEM already exists, skipping: {out_path}")
        return out_path

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with rasterio.open(dem_path) as src:
        # Reproject AOI to DEM CRS and add buffer
        aoi_reproj   = aoi_gdf.to_crs(src.crs)
        aoi_buffered = aoi_reproj.buffer(buffer_m)

        clipped, transform = mask(src, aoi_buffered.geometry, crop=True)
        meta = src.meta.copy()
        meta.update({
            "height"   : clipped.shape[1],
            "width"    : clipped.shape[2],
            "transform": transform
        })

    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(clipped)

    with rasterio.open(out_path) as src:
        print(f"Clipped DEM shape: {src.shape}")

    print(f"Clipped DEM saved: {out_path}")
    return out_path

