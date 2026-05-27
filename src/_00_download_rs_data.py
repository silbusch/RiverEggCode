# src/_00_download_rs_data.py
#=============================================================

# Purpose: **Purpose:** Download data for a defined AOI, without downloading
# the full global datasets. Two approaches are implemented:

# (SWOT) Surface Water and Ocean Topography 
# HYDROCRON API - single reach query function

# https://podaac.github.io/hydrocron/user-guide/fields/

# REACH FIELDS:
#
#   'reach_id', 'time', 'time_tai', 'time_str', 'p_lat', 'p_lon', 'river_name',
#   'wse',      'wse_u', 'wse_r_u', 'wse_c', 'wse_c_u',
#   'slope',    'slope_u', 'slope_r_u', 'slope2', 'slope2_u', 'slope2_r_u',
#   'width',    'width_u', 'width_c', 'width_c_u',
#   'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
#   'd_x_area', 'd_x_area_u',
#   'layovr_val', 'node_dist', 'loc_offset', 'xtrk_dist',
#   'dschg_c', 'dschg_c_u', 'dschg_csf', 'dschg_c_q',
#   'dschg_gc', 'dschg_gc_u', 'dschg_gcsf', 'dschg_gc_q',
#   'dschg_m', 'dschg_m_u', 'dschg_msf', 'dschg_m_q',
#   'dschg_gm', 'dschg_gm_u', 'dschg_gmsf', 'dschg_gm_q',
#   'dschg_b', 'dschg_b_u', 'dschg_bsf', 'dschg_b_q',
#   'dschg_gb', 'dschg_gb_u', 'dschg_gbsf', 'dschg_gb_q',
#   'dschg_h', 'dschg_h_u', 'dschg_hsf', 'dschg_h_q',
#   'dschg_gh', 'dschg_gh_u', 'dschg_ghsf', 'dschg_gh_q',
#   'dschg_o', 'dschg_o_u', 'dschg_osf', 'dschg_o_q',
#   'dschg_go', 'dschg_go_u', 'dschg_gosf', 'dschg_go_q',
#   'dschg_s', 'dschg_s_u', 'dschg_ssf', 'dschg_s_q',
#   'dschg_gs', 'dschg_gs_u', 'dschg_gssf', 'dschg_gs_q',
#   'dschg_i', 'dschg_i_u', 'dschg_isf', 'dschg_i_q',
#   'dschg_gi', 'dschg_gi_u', 'dschg_gisf', 'dschg_gi_q',
#   'dschg_q_b', 'dschg_gq_b',
#   'reach_q', 'reach_q_b',
#   'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_nod',
#   'obs_frac_n', 'xovr_cal_q', 'geoid_hght', 'geoid_slop',
#   'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
#   'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c',
#   'n_reach_up', 'n_reach_dn', 'rch_id_up', 'rch_id_dn',
#   'p_wse', 'p_wse_var', 'p_width', 'p_wid_var', 'p_n_nodes', 'p_dist_out',
#   'p_length', 'p_maf', 'p_dam_id', 'p_n_ch_max', 'p_n_ch_mod', 'p_low_slp',
#   'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
#   'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
#   'granuleUR', 'ingest_time'

#### NODE FIELDS: ##########################################
#
# 'reach_id', 'node_id', 'time', 'time_tai', 'time_str',
# 'lat', 'lon', 'lat_u', 'lon_u', 'river_name',
# 'wse', 'wse_u', 'wse_r_u',
# 'wse_sm', 'wse_sm_u', 'wse_sm_q', 'wse_sm_q_b',
# 'width', 'width_u',
# 'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
# 'layovr_val', 'node_dist', 'xtrk_dist',
# 'flow_angle', 'node_q', 'node_q_b',
# 'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'n_good_pix',
# 'xovr_cal_q', 'rdr_sig0', 'rdr_sig0_u', 'rdr_pol',
# 'geoid_hght', 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
# 'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c',
# 'p_wse', 'p_wse_var', 'p_width', 'p_wid_var', 'p_dist_out', 'p_length',
# 'p_dam_id', 'p_n_ch_max', 'p_n_ch_mod',
# 'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
# 'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
# 'granuleUR', 'ingest_time'
#
# ============================================================

import requests
import earthaccess
import zipfile
import os
import io 
import tempfile 
import geopandas as gpd
import pandas as pd
import time
import math
from soilgrids import SoilGrids
import rasterio

# ============================================================
# HYDROCRON API
# ============================================================

HYDROCRON_BASE_URL = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"

def query_hydrocron_reach(reach_id, start_time, end_time, fields, output_format="geojson"):
    """
    Query the Hydrocron API for a single SWORD reach.
    IMPORTANT: Hydrocron reach_id format:

    Hydrocron uses SWORD reach IDs. The ID must be exactly 11 digits.
    SWORD v17b IDs are already 11 digits (e.g. 46219400056).
    If the IDs differ, -> Need to check the used SWORD version.

    SWOT coverage limitations: SWOT observes rivers wider than ca.

    Parameters:
    -----------
    reach_id      : str  - SWORD reach identifier (11 digits)
    start_time    : str  - ISO 8601 start (e.g. '2023-08-01T00:00:00Z'
    end_time      : str  - ISO 8601 end
    fields        : str  - comma-separated list of SWOT fields
    output_format : str  - 'geojson' or 'csv'

    Returns:
    --------
    dict  - always returns a dict with keys:

            'status'  : 'ok' | 'no_data' | 'error'
            'data'    : parsed response JSON (or None)
            'message' : status string
    """
    params = {
        "feature": "Reach",
        "feature_id": str(reach_id),
        "start_time": start_time,
        "end_time": end_time,
        "output": output_format,
        "fields": fields
    }

    try:
        response = requests.get(HYDROCRON_BASE_URL, params=params, timeout=30)

        # Parse body regardless of status code
        # Hydrocron uses 400 for both invalid requests AND missing data.
        try:
            body = response.json()
        except Exception:
            body = {"detail": response.text}

        if response.status_code == 200:
            return {"status": "ok", "data": body, "message": "success"}

        if response.status_code == 400:
            # Distinguish: no data vs. malformed request
            msg = str(body.get("detail", body.get("message", ""))).lower()
            if any(kw in msg for kw in ["no data", "not found", "no results", "no time series"]):
                return {"status": "no_data", "data": None, "message": msg}

            return {"status": "error", "data": None,
                    "message": f"400 Bad Request: {body}"}

        return {"status": "error", "data": None,
                "message": f"HTTP {response.status_code}: {body}"}

    except requests.exceptions.Timeout:
        return {"status": "error", "data": None,
                "message": f"Timeout for reach {reach_id}"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "data": None, "message": str(e)}
    

def parse_hydrocron_results(all_features):
    """
    Convert raw Hydrocron GeoJSON features into a clean GeoDataFrame.
    Converts time column to datetime, numeric columns to float,
    and replaces SWOT nodata values with NaN.

    Parameters:
    -----------
    all_features : list - GeoJSON features collected from Hydrocron API

    Returns:
    --------
    GeoDataFrame or None if all_features is empty
    """

    # Return None if nothing to parse
    if not all_features:
        print("No features to parse.")
        return None

    # build GeoDataFrame from GeoJSON features:
    gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")

    # Step 3: convert time column to datetime
    if "time_str" in gdf.columns:
        gdf["time_str"] = pd.to_datetime(gdf["time_str"], errors="coerce", utc=True)

    # Convert numeric columns to float and replace SWOT nodata with NaN:
    # SWOT uses -999999999999 as nodata value
    SWOT_NODATA = -999999999999

    for col in ["wse", "slope", "width"]:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce").astype("float64")
            gdf[col] = gdf[col].where(gdf[col] > SWOT_NODATA)

    print(f"Observations parsed: {len(gdf)}")
    print(f"Columns: {gdf.columns.tolist()}")
    
    return gdf


def query_hydrocron_bulk(sword, start_time, end_time, fields,
                         min_width_m=100,
                         output_format="geojson",
                         request_delay=0.3):
    """
    Query the Hydrocron API for all SWORD reaches in a GeoDataFrame.
    Skips reaches narrower than min_width_m (SWOT observes rivers > ca. 100m wide).
    Collects all returned GeoJSON features into a single list.

    Parameters:
    -----------
    sword          : GeoDataFrame - clipped SWORD reaches (from Notebook 01)
    start_time     : str - ISO 8601 start time (e.g. '2023-08-01T00:00:00Z')
    end_time       : str - ISO 8601 end time
    fields         : str - comma-separated SWOT fields to retrieve
    min_width_m    : float - skip reaches narrower than this (default: 100m)
    output_format  : str - 'geojson' or 'csv' (default: 'geojson')
    request_delay  : float - seconds to wait between API calls (default: 0.3)

    Returns:
    --------
    list : GeoJSON features collected from all queried reaches
    """
    # Filter reaches by minimum width to avoid unnecessary API calls
    # SWOT cannot observe rivers narrower than ~100m
    if "width" in sword.columns and min_width_m > 0:
        query_reaches = sword[sword["width"] >= min_width_m]["reach_id"].astype(str).tolist()
        skipped = len(sword) - len(query_reaches)
        print(f"Reaches queried (width >= {min_width_m}m): {len(query_reaches)}")
        print(f"Skipped (too narrow): {skipped}")
    else:
        query_reaches = sword["reach_id"].astype(str).tolist()
        print(f"Querying all {len(query_reaches)} reaches (no width filter applied)")

    print(f"Time range: {start_time} → {end_time}")

    # Query each reach individually via Hydrocron API
    all_features = []
    n_ok, n_no_data, n_error = 0, 0, 0
    # collect errors for review after the loop
    error_log = []

    for i, rid in enumerate(query_reaches):
        if i % 10 == 0:
            print(f"{i:3d}/{len(query_reaches)} | ok={n_ok} no_data={n_no_data} error={n_error}")

        result = query_hydrocron_reach(
            reach_id = rid,
            start_time = start_time,
            end_time = end_time,
            fields= fields,
            output_format = output_format
        )

        if result["status"] == "ok":
            try:
                features = result["data"]["results"]["geojson"]["features"]
                if features:
                    all_features.extend(features)
                    n_ok += 1
                else:
                    n_no_data += 1
            except (KeyError, TypeError):
                n_error += 1
                error_log.append((rid, "unexpected response structure"))

        elif result["status"] == "no_data":
            n_no_data += 1

        else:
            n_error += 1
            error_log.append((rid, result["message"]))

        # Small delay to avoid overloading the API
        time.sleep(request_delay)

    print(f"\nDone. ok={n_ok} | no_data={n_no_data} | errors={n_error}")
    print(f"Total observations collected: {len(all_features)}")

    if error_log:
        print(f"\nError log (first 10):")
        for rid, msg in error_log[:10]:
            print(f"  reach {rid}: {msg}")

    return all_features


# ============================================================
# EARTHACCESS
# ============================================================

def compute_bbox(gdf, pad=0.05):
    """
    Creating a bounding box with small buffer around SWORD AOI and return as tuple.
    The Buffer is created to not cut off reaches at the edges.

    Parameters:
    -----------
    gdf : GeoDataFrame - input vector dataset to compute bounds from
    pad : float        - padding in degrees added to each side (default: 0.05) 

    Returns:
    --------
    tuple : (min_lon, min_lat, max_lon, max_lat) with buffer applied 
    """
    # Load SWORD clip and derive make box
    bounds = gdf.total_bounds
    bbox = (
        bounds[0] - pad, # min_lon
        bounds[1] - pad, # min_lat
        bounds[2] + pad, # max_lon
        bounds[3] + pad  # max_lat
    )
    print(f"\nAuto-computed bbox (with {pad} buffer):")
    print(f"  (lon_min={bbox[0]:.4f}, lat_min={bbox[1]:.4f}, "
        f"lon_max={bbox[2]:.4f}, lat_max={bbox[3]:.4f})")
    
    return bbox


def search_swot_granules(collection, bbox, start_time, end_time):
    """
    Search NASA earthaccess for SWOT granules filtered by collection, 
    bounding box, and time range.

    Parameters:
    -----------
    collection : str - e.g. "SWOT_L2_HR_RiverSP_reach_D"
    bbox : tuple - (min_lon, min_lat, max_lon, max_lat) with buffer applied
    start_time: str - Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
    end_time: str - Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)

    Returns:
    --------
    list : list of earthaccess DataGranule objects, or empty list if none found
    """
    # Search for granules matching collection, bbox and time range
    # NOTE: The bounding box filters which satellite passes intersect
    # the AOI, NOT which features within the pass are inside it.
    # Each granule still covers a full continent pass.
    results = earthaccess.search_data(
        short_name = collection,
        bounding_box = bbox,
        temporal = (start_time, end_time),
        count = -1
    )   
    
    if results:
        print(f"First: {results[0]['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']}")
        print(f"Last : {results[-1]['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']}")
        print(f"Granules found: {len(results)}")
        # Estimate data volume
        est_mb_per_granule = 80 # rough estimation
        est_total_gb = len(results) * est_mb_per_granule/ 1000
        print(f"\nEstimated download size (if all downloaded): ca. {est_total_gb:.0f} GB")
    else:
        print("No granules found for the given parameters.")
    
    return results


def stream_swot_granules(results, aoi_bounds,
                         max_granules=None,
                        granule_stride=1):
    """
    Stream SWOT granules in-memory, clip to AOI bounding box, and return
    a merged GeoDataFrame. No files are written to disk.

    Parameters:
    -----------
    results        : list - granule results from earthaccess.search_data()
    aoi_bounds     : array-like - (minx, miny, maxx, maxy) for spatial clip
    max_granules   : int or None - max number of granules to process (None = all)
    granule_stride : int - process every Nth granule (1 = every granule)

    Returns:
    --------
    GeoDataFrame or None if no AOI features found
    """
    
    # Build the list of granules to process
    process_list = results[::granule_stride]
    if max_granules:
        process_list = process_list[:max_granules]

    print(f"Granules to process : {len(process_list)} of {len(results)}")
    print(f"Stride: {granule_stride}")
    print(f"AOI bounds: {aoi_bounds.round(4)}")

    # Open an authenticated session for streaming
    # earthaccess.get_requests_https_session() returns a requests.Session
    # with NASA EDL credentials pre-configured.
    session = earthaccess.get_requests_https_session()

    all_clipped= []   #list of clipped GeoDataFrames
    n_ok = 0
    n_empty = 0
    n_error = 0

    for i, granule in enumerate(process_list):
        if i % 50 == 0:
            print(f"{i:4d}/{len(process_list)} | ok={n_ok} empty={n_empty} error={n_error}")

        # Get the direct HTTPS download URL for this granule
        try:
            urls = granule.data_links(access="external")
            if not urls:
                # Fallback: extract URL from umm metadata directly
                related = granule['umm'].get('RelatedUrls', [])
                urls = [
                    r['URL'] for r in related
                    if r.get('Type') == 'GET DATA' and r['URL'].endswith('.zip')
                ]
            if not urls:
                n_error += 1
                continue
            zip_url = urls[0]
        except Exception as e:
            n_error += 1
            continue

        try:
            # Stream the ZIP into memory (no disk write)
            response = session.get(zip_url, timeout=60)
            response.raise_for_status()

            zip_buffer = io.BytesIO(response.content)

            # Find the Shapefile inside the ZIP
            with zipfile.ZipFile(zip_buffer) as zf:
                shp_names = [n for n in zf.namelist() if n.endswith('.shp')]
                if not shp_names:
                    n_empty += 1
                    continue

                # Read shapefile directly from the in-memory ZIP
                # Reset buffer so geopandas can re-read from it
                zip_buffer.seek(0)

            # geopandas zip:// URI syntax works with BytesIO via a temp path trick
            # Write ZIP to a small NamedTemporaryFile, read, then delete
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp.write(zip_buffer.getvalue())
                tmp_path = tmp.name

            try:
                gdf = gpd.read_file(f"zip://{tmp_path}!{shp_names[0]}")
            finally:
                os.unlink(tmp_path)   # delete temp file immediately after reading

            # Clip to AOI bounding box
            clipped = gdf.cx[
                aoi_bounds[0]:aoi_bounds[2],
                aoi_bounds[1]:aoi_bounds[3]
            ]

            if not clipped.empty:
                # Add observation timestamp from granule metadata
                clipped = clipped.copy()
                clipped["granule_time"] = granule['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']
                all_clipped.append(clipped)
                n_ok += 1
            else:
                n_empty += 1

        except Exception as e:
            n_error += 1
            if n_error <= 5:
                print(f"Error on granule {i}: {e}")

    print("-" * 55)
    print(f"Done.")
    print(f"Granules with AOI data : {n_ok}")
    print(f"Granules empty (no AOI hit) : {n_empty}")
    print(f"Errors: {n_error}")

    # Merge and save
    if all_clipped:   
        return gpd.GeoDataFrame(
            pd.concat(all_clipped, ignore_index=True),
            crs=all_clipped[0].crs)
    else:    
        print("\nNo AOI features found across all processed granules.")
        print("Possible causes:")
        print("- SWOT did not observe this AOI in the selected time range")
        print("- River reaches are narrower than the SWOT 100 m threshold")
        print("- Bounding box does not intersect SWOT pass coverage")
        return None


# ============================================================
# ESA
# ============================================================

# WORLDCOVER

def download_worldcover(bbox, 
                        out_dir,
                        max_tiles = 10):
    """
    Download ESA WorldCover 2021 (10m) tiles for a given bounding box.
    Tiles are downloaded from the public AWS S3 bucket (no login required).
    Only tiles intersecting the bbox are downloaded.

    Parameters:
    -----------
    bbox        : tuple : (min_lon, min_lat, max_lon, max_lat) with buffer applied 
    out_dir     : str - directory where downloaded tiles are saved
    max_tiles   : int - max. amount of tiles before warning

    Returns:
    --------
    list : file paths of downloaded GeoTIFF tiles
    """

    # Base URL for AWS S3 public bucket
    BASE_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

    # Compute which 3x3 degree tiles intersect the bbox
    # Tiles are named by their lower-left corner, snapped to 3-degree grid
    # e.g. bbox covering lon 71-78, lat 40-42 needs tiles at:
    # lon: 72, 75 (floor to nearest 3)
    # lat: 39 (floor to nearest 3)
    
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # snap to 3-degree grid (floor division)
    lon_start = math.floor(min_lon / 3) * 3
    lat_start = math.floor(min_lat / 3) * 3
    
    # build list of all tile corners needed
    tile_origins = []
    lon = lon_start
    while lon < max_lon:
        lat = lat_start
        while lat < max_lat:
            tile_origins.append((lon, lat))
            lat += 3
        lon += 3
    
    print(f"Tiles needed: {len(tile_origins)}")
    # Safety check to avoid accidental large downloads
    if len(tile_origins) > max_tiles:
        raise ValueError(
            f"Too many tiles ({len(tile_origins)}) for bbox. "
            f"Increase max_tiles or reduce bbox. Current limit: {max_tiles}"
        )
    for t in tile_origins:
        print(f"  lon={t[0]}, lat={t[1]}")

    def tile_name(lon, lat):
        """Build WorldCover tile name from lower-left corner coordinates."""
        lat_str = f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}"
        lon_str = f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
        return f"{lat_str}{lon_str}" 
    
    os.makedirs(out_dir, exist_ok=True)
    downloaded = []  # collect paths of successfully downloaded files

    for lon, lat in tile_origins:
        name = tile_name(lon, lat)
        filename = f"ESA_WorldCover_10m_2021_v200_{name}_Map.tif"
        url = f"{BASE_URL}/{filename}"
        out_path = os.path.join(out_dir, filename)

        # Skip if already downloaded
        if os.path.exists(out_path):
            print(f"Already exists, skipping: {filename}")
            downloaded.append(out_path)
            continue

        # Download tile
        print(f"Downloading: {filename}")
        response = requests.get(url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Saved: {out_path}")
            downloaded.append(out_path)
        else:
            print(f"Not found (HTTP {response.status_code}): {url}")

    print(f"\nDownload complete: {len(downloaded)} tiles")
    return downloaded   


def merge_raster_tiles(tile_paths, out_path):
    """
    Merge multiple raster tiles into a single GeoTIFF mosaic.
    Used to combine WorldCover tiles before joining to SWORD reaches.

    Parameters:
    -----------
    tile_paths : list - file paths of individual raster tiles to merge
    out_path   : str  - file path for the merged output GeoTIFF

    Returns:
    --------
    str : file path of the merged GeoTIFF
    """
    from rasterio.merge import merge as rio_merge

    # Skip if already merged
    if os.path.exists(out_path):
        print(f"Already exists, skipping merge: {out_path}")
        return out_path

    print(f"Merging {len(tile_paths)} tiles...")

    # Open all source tiles
    sources = [rasterio.open(p) for p in tile_paths]

    # Merge into one mosaic
    mosaic, transform = rio_merge(sources)

    # Copy metadata from first tile and update with new dimensions
    meta = sources[0].meta.copy()
    meta.update({
        "driver"    : "GTiff",
        "height"    : mosaic.shape[1],
        "width"     : mosaic.shape[2],
        "transform" : transform
    })

    # Save merged raster
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with rasterio.open(out_path, "w", **meta) as dest:
        dest.write(mosaic)

    # Close all source files
    for src in sources:
        src.close()

    print(f"Merged {len(tile_paths)} tiles → {out_path}")
    return out_path


# ============================================================
# SoilGrids
# ============================================================
# https://docs.isric.org/globaldata/soilgrids/


def download_soilgrids(bbox, 
                        out_dir,
                        soilgrids_vars):
    """
    Download SoilGrids (250m) tiles for a given bounding box.
    

    Parameters:
    -----------
    bbox        : tuple : (min_lon, min_lat, max_lon, max_lat) with buffer applied 
    out_dir     : str - directory where downloaded tiles are saved
    soilgrids_vars: list of tuples - (service_id, coverage_id, description)

    Returns:
    --------
    list : file paths of downloaded GeoTIFF tiles
    """
    soil_grids = SoilGrids()

    downloaded = []
    os.makedirs(out_dir, exist_ok=True)

    # SoilGrids native resolution is 250m
    # At EPSG:4326, roughly 0.002° per pixel (250m / ~111000m per degree)
    RESOLUTION_DEG = 250 / 111000  # degrees per pixel

    width  = int((bbox[2] - bbox[0]) / RESOLUTION_DEG)  # lon extent / resolution
    height = int((bbox[3] - bbox[1]) / RESOLUTION_DEG)  # lat extent / resolution

    print(f"Requesting grid: {width} x {height} pixels")

    for service_id, coverage_id, description in soilgrids_vars:
        out_path = os.path.join(out_dir, f"{coverage_id}.tif")
        
        # Skip if already downloaded
        if os.path.exists(out_path):
            print(f"Already exists, skipping: {coverage_id}")
            downloaded.append(out_path)
            continue
        
        print(f"Downloading: {coverage_id} – {description}")
        soil_grids.get_coverage_data(
            service_id  = service_id,
            coverage_id = coverage_id,
            west  = float(bbox[0]),
            south = float(bbox[1]),
            east  = float(bbox[2]),
            north = float(bbox[3]),
            crs    = "urn:ogc:def:crs:EPSG::4326",
            width  = width,
            height = height,
            output = out_path
        )
        downloaded.append(out_path)
        print(f"  Saved: {out_path}")

    print(f"\nDownload complete: {len(downloaded)} variables")
    return downloaded