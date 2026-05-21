# src/_0_download_rs.py
#=============================================================
# 0.1. (SWOT) Surface Water and Ocean Topography 



# ============================================================

# https://podaac.github.io/hydrocron/user-guide/fields/

#### REACH FIELDS: ##########################################
#
# 'reach_id', 'time', 'time_tai', 'time_str', 'p_lat', 'p_lon', 'river_name',
# 'wse', 'wse_u', 'wse_r_u', 'wse_c', 'wse_c_u',
# 'slope', 'slope_u', 'slope_r_u', 'slope2', 'slope2_u', 'slope2_r_u',
# 'width', 'width_u', 'width_c', 'width_c_u',
# 'area_total', 'area_tot_u', 'area_detct', 'area_det_u', 'area_wse',
# 'd_x_area', 'd_x_area_u',
# 'layovr_val', 'node_dist', 'loc_offset', 'xtrk_dist',
# 'dschg_c', 'dschg_c_u', 'dschg_csf', 'dschg_c_q',
# 'dschg_gc', 'dschg_gc_u', 'dschg_gcsf', 'dschg_gc_q',
# 'dschg_m', 'dschg_m_u', 'dschg_msf', 'dschg_m_q',
# 'dschg_gm', 'dschg_gm_u', 'dschg_gmsf', 'dschg_gm_q',
# 'dschg_b', 'dschg_b_u', 'dschg_bsf', 'dschg_b_q',
# 'dschg_gb', 'dschg_gb_u', 'dschg_gbsf', 'dschg_gb_q',
# 'dschg_h', 'dschg_h_u', 'dschg_hsf', 'dschg_h_q',
# 'dschg_gh', 'dschg_gh_u', 'dschg_ghsf', 'dschg_gh_q',
# 'dschg_o', 'dschg_o_u', 'dschg_osf', 'dschg_o_q',
# 'dschg_go', 'dschg_go_u', 'dschg_gosf', 'dschg_go_q',
# 'dschg_s', 'dschg_s_u', 'dschg_ssf', 'dschg_s_q',
# 'dschg_gs', 'dschg_gs_u', 'dschg_gssf', 'dschg_gs_q',
# 'dschg_i', 'dschg_i_u', 'dschg_isf', 'dschg_i_q',
# 'dschg_gi', 'dschg_gi_u', 'dschg_gisf', 'dschg_gi_q',
# 'dschg_q_b', 'dschg_gq_b',
# 'reach_q', 'reach_q_b',
# 'dark_frac', 'ice_clim_f', 'ice_dyn_f', 'partial_f', 'n_good_nod',
# 'obs_frac_n', 'xovr_cal_q', 'geoid_hght', 'geoid_slop',
# 'solid_tide', 'load_tidef', 'load_tideg', 'pole_tide',
# 'dry_trop_c', 'wet_trop_c', 'iono_c', 'xovr_cal_c',
# 'n_reach_up', 'n_reach_dn', 'rch_id_up', 'rch_id_dn',
# 'p_wse', 'p_wse_var', 'p_width', 'p_wid_var', 'p_n_nodes', 'p_dist_out',
# 'p_length', 'p_maf', 'p_dam_id', 'p_n_ch_max', 'p_n_ch_mod', 'p_low_slp',
# 'cycle_id', 'pass_id', 'continent_id', 'range_start_time', 'range_end_time',
# 'crid', 'geometry', 'sword_version', 'collection_shortname', 'collection_version',
# 'granuleUR', 'ingest_time'

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

# ============================================================
# HYDROCRON API - single reach query function

# ============================================================

import requests


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
