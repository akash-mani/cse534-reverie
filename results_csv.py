#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverie RDMA-TCP Buffer Management Simulation Analysis
Reads raw dump files from <basePath>/dumps/
Writes processed CSV results to <basePath>/results/
"""

import numpy as np
# import matplotlib.pyplot as plt # Not used in this script version
import pandas as pd
import os
import sys
import argparse # Added for CLI arguments
from typing import List, Dict, Tuple, Optional, Any

# Constants and Configuration Classes
class BufferAlgs:
    DT = 101
    FAB = 102
    ABM = 110
    REVERIE = 111

    @classmethod
    def get_all(cls) -> List[str]:
        return [str(cls.DT), str(cls.ABM), str(cls.REVERIE)]

    @classmethod
    def get_names(cls) -> Dict[str, str]:
        return { str(cls.DT): "DT", str(cls.ABM): "ABM", str(cls.REVERIE): "Reverie" }

    # Colors and Markers removed as they are for plotting script

class CongestionControl:
    # RDMA CCs
    DCQCNCC = 1
    INTCC = 3 # Also represents PowerTCP in some experiments
    TIMELYCC = 7
    PINTCC = 10
    # TCP CCs
    CUBIC = 2
    DCTCP = 4

    # Mapping for CLI arg -> code
    TCP_CC_MAP = {
        "CUBIC": CUBIC,
        "DCTCP": DCTCP
    }
    @classmethod
    def get_tcp_cc_code(cls, name: str) -> str:
        """Get the integer code for a TCP CC name."""
        code = cls.TCP_CC_MAP.get(name.upper())
        if code is None:
            raise ValueError(f"Unknown TCP CC: {name}. Valid options: {list(cls.TCP_CC_MAP.keys())}")
        return str(code)

# Directories class removed - paths are now dynamic

class SimulationParams:
    # Default buffer size is calculated in main based on --numPorts CLI arg
    DEFAULT_BUFFER_KB_PER_PORT_GBPS = 5.12 # Default value (Tomahawk-like)
    LOADS = ["0.2", "0.4", "0.6", "0.8"]
    LOADS_FLOAT = [0.2, 0.4, 0.6, 0.8]
    # Bursts used when varying RDMA burst size (Exp 2, 8, 9)
    RDMA_BURST_SIZES_VAR = ["500000", "1000000", "1500000", "2500000"] # Skips 2M (as per original script's analysis)
    # Bursts used when varying TCP burst size (Exp 4)
    TCP_BURST_SIZES_VAR = ["12500", "500000", "1000000", "2000000"] # Skips 1.5M (as per original script's analysis)
    LOSSY_FRACTIONS = ["0.2", "0.4", "0.6", "0.8"]
    GAMMA_VALUES = ["0.4", "0.8", "0.9", "0.99", "0.999", "0.999999"]
    # Values for the varying buffer size experiment (Exp 12)
    BUFFER_SIZES_KB_PER_PORT_GBPS = ["3.44", "5.12", "7", "9.6"]
    # Constants for buffer size calculation (can be overridden for Exp 12)
    DEFAULT_PORTS = 10 # Default number of ports for buffer calculation
    DEFAULT_PORT_SPEED_GBPS = 25 # Default port speed

# --- Utility Functions ---
def ensure_directories_exist(directories: List[str]) -> None:
    """Create directories if they don't exist."""
    for directory in directories:
        # Use exist_ok=True to avoid error if directory already exists
        os.makedirs(directory, exist_ok=True)
        # Check if creation was successful or if it already existed
        if os.path.isdir(directory):
             if directory not in getattr(ensure_directories_exist, 'created_dirs', set()):
                  print(f"Directory ensured: {directory}")
                  if not hasattr(ensure_directories_exist, 'created_dirs'):
                      ensure_directories_exist.created_dirs = set()
                  ensure_directories_exist.created_dirs.add(directory)
        else:
             print(f"ERROR: Failed to create directory: {directory}")


def get_file_path(base_path: str, file_type: str, params: Dict[str, str]) -> str:
    """Generate full input dump file path based on experiment parameters."""
    dump_subdir = "dumps" # Relative name of the dump directory
    base_filename = f"evaluation-{params['alg']}-{params['rdmacc']}-{params['tcpcc']}-{params['rdmaload']}-{params['tcpload']}-{params['rdmaburst']}-{params['tcpburst']}-{params['egresslossyFrac']}-{params['gamma']}"

    if file_type == "fct": filename = f"{base_filename}.fct"
    elif file_type == "tor": filename = f"{base_filename}.tor"
    elif file_type == "out": filename = f"{base_filename}.out"
    elif file_type == "pfc": filename = f"{base_filename}.pfc"
    else: raise ValueError(f"Unknown file type: {file_type}")

    return os.path.join(base_path, dump_subdir, filename)


def get_buffer_file_path(base_path: str, file_type: str, params: Dict[str, str]) -> str:
    """Generate full input dump file path for buffer size experiments."""
    dump_subdir = "dumps" # Relative name of the dump directory
    # Note: 'buffer_kb_gbps' key holds the specific buffer value string for the filename
    base_filename = f"buffer-{params['alg']}-{params['rdmacc']}-{params['tcpcc']}-{params['rdmaload']}-{params['tcpload']}-{params['rdmaburst']}-{params['tcpburst']}-{params['egresslossyFrac']}-{params['gamma']}-{params['buffer_kb_gbps']}"

    if file_type == "fct": filename = f"{base_filename}.fct"
    elif file_type == "tor": filename = f"{base_filename}.tor"
    elif file_type == "out": filename = f"{base_filename}.out"
    elif file_type == "pfc": filename = f"{base_filename}.pfc"
    else: raise ValueError(f"Unknown file type: {file_type}")

    return os.path.join(base_path, dump_subdir, filename)


def write_to_csv(output_dir_path: str, title: str, headers: List[str], data: List[List[Any]], filename: str) -> None:
    """Write experiment results to a CSV file in the specified output directory."""
    filepath = os.path.join(output_dir_path, filename)
    try:
        df = pd.DataFrame(data, columns=headers)
        df.to_csv(filepath, index=False, float_format='%.5g', na_rep='NaN') # Consistent float format
        print(f"Results written to {filepath}")
    except Exception as e:
        print(f"ERROR writing CSV to {filepath}: {e}")


# --- Analysis Functions ---
def analyze_fct_data(fct_file: str, incast: Optional[bool] = None, priority: Optional[int] = None,
                    flowsize_filter: Optional[Tuple[Optional[int], Optional[int]]] = None) -> Dict[str, Any]:
    """
    Analyze flow completion time data from raw .fct files.
    Returns slowdown and raw FCT (us) stats.
    Percentiles return np.nan if insufficient data points.
    """
    results = {
        "slowdown_avg": np.nan, "slowdown_median": np.nan, "slowdown_p95": np.nan,
        "slowdown_p99": np.nan, "slowdown_p999": np.nan,
        "fct_us_avg": np.nan, "fct_us_median": np.nan, "fct_us_p95": np.nan,
        "fct_us_p99": np.nan, "fct_us_p999": np.nan,
        "count": 0
    }
    try:
        if not os.path.exists(fct_file) or os.path.getsize(fct_file) == 0:
            # print(f" Warning: FCT file not found or empty: {fct_file}") # Reduce noise
            return results

        # Read space-delimited FCT file, handle potential missing header or comments
        try:
             fct_df = pd.read_csv(fct_file, delimiter=' ', comment='#', header=None, skipinitialspace=True, low_memory=False,
                                  names=["timestamp", "flowsize", "fctus", "basefctus", "slowdown", "baserttus", "priority", "incastflow"])
        except pd.errors.EmptyDataError:
             # print(f" Warning: FCT file is empty: {fct_file}")
             return results
        except Exception as read_e:
             print(f" Error reading FCT file {fct_file}: {read_e}")
             return results


        if fct_df.empty: return results

        # --- Data Cleaning ---
        # Ensure numeric types where expected, coerce errors to NaN
        for col in ["timestamp", "flowsize", "fctus", "basefctus", "slowdown", "baserttus", "priority", "incastflow"]:
            if col in fct_df.columns:
                fct_df[col] = pd.to_numeric(fct_df[col], errors='coerce')
        fct_df.dropna(subset=["flowsize", "fctus", "basefctus", "slowdown", "priority", "incastflow"], inplace=True) # Drop rows where essential data is missing/invalid


        filter_conditions = []
        if incast is not None: filter_conditions.append(fct_df["incastflow"] == (1 if incast else 0))
        if priority is not None: filter_conditions.append(fct_df["priority"] == priority)
        if flowsize_filter:
            min_size, max_size = flowsize_filter
            if min_size is not None: filter_conditions.append(fct_df["flowsize"] > min_size)
            if max_size is not None: filter_conditions.append(fct_df["flowsize"] < max_size)

        if filter_conditions:
            combined_filter = filter_conditions[0]; [combined_filter := combined_filter & c for c in filter_conditions[1:]]
            filtered_df = fct_df[combined_filter].copy()
        else: filtered_df = fct_df.copy()

        if filtered_df.empty: return results
        results["count"] = len(filtered_df)

        if "slowdown" in filtered_df.columns:
            slowdowns = filtered_df["slowdown"].dropna().tolist()
            if slowdowns:
                slowdowns = [s for s in slowdowns if s > 0 and np.isfinite(s)] # Filter out non-positive/inf slowdowns
                if slowdowns:
                    slowdowns.sort()
                    results["slowdown_avg"]=np.mean(slowdowns); results["slowdown_median"]=np.median(slowdowns)
                    results["slowdown_p95"]=np.percentile(slowdowns, 95) if len(slowdowns) >= 20 else np.nan
                    results["slowdown_p99"]=np.percentile(slowdowns, 99) if len(slowdowns) >= 100 else np.nan
                    results["slowdown_p999"]=np.percentile(slowdowns, 99.9) if len(slowdowns) >= 1000 else np.nan

        if "fctus" in filtered_df.columns:
             fcts_us = filtered_df["fctus"].dropna().tolist()
             if fcts_us:
                 fcts_us = [f for f in fcts_us if f >= 0 and np.isfinite(f)] # Filter out negative/inf fcts
                 if fcts_us:
                     fcts_us.sort()
                     results["fct_us_avg"]=np.mean(fcts_us); results["fct_us_median"]=np.median(fcts_us)
                     results["fct_us_p95"]=np.percentile(fcts_us, 95) if len(fcts_us) >= 20 else np.nan
                     results["fct_us_p99"]=np.percentile(fcts_us, 99) if len(fcts_us) >= 100 else np.nan
                     results["fct_us_p999"]=np.percentile(fcts_us, 99.9) if len(fcts_us) >= 1000 else np.nan
        return results
    except Exception as e: print(f"Error analyzing FCT file {fct_file}: {e}"); return results

def analyze_pfc_data(pfc_file: str) -> Dict[str, Any]:
    results = {"count": 0, "has_pauses": False}
    try:
        if not os.path.exists(pfc_file) or os.path.getsize(pfc_file) == 0: return results
        # Read space-delimited PFC file
        try:
            pfc_df = pd.read_csv(pfc_file, delimiter=' ', comment='#', header=None, skipinitialspace=True, low_memory=False,
                                 names=["Time", "NodeId", "NodeType", "IfIndex", "type"])
        except pd.errors.EmptyDataError:
             return results
        except Exception as read_e:
             print(f" Error reading PFC file {pfc_file}: {read_e}")
             return results

        if pfc_df.empty: return results
        results["count"] = len(pfc_df); results["has_pauses"] = len(pfc_df) > 0
        return results
    except Exception as e: print(f"Error analyzing PFC file {pfc_file}: {e}"); return results

def analyze_tor_data(tor_file: str, buffer_size_bytes: int) -> Dict[str, Any]:
    """
    Analyze ToR (buffer usage) data from raw .tor files.
    Returns percentages and raw bytes stats.
    """
    results = {
        "lossy_p99_pct": np.nan, "lossless_p99_pct": np.nan, "total_p99_pct": np.nan,
        "lossy_avg_pct": np.nan, "lossless_avg_pct": np.nan, "total_avg_pct": np.nan,
        "headroom_p99_bytes": np.nan, "headroom_avg_bytes": np.nan,
        "shared_p99_bytes": np.nan, "shared_avg_bytes": np.nan
    }
    try:
        if not os.path.exists(tor_file) or os.path.getsize(tor_file) == 0: return results
        if buffer_size_bytes <= 0: print(f"Warning: Invalid buffer_size_bytes ({buffer_size_bytes}) for TOR file {tor_file}. Cannot calculate percentages."); buffer_size_bytes = 1
        # Read space-delimited TOR file
        try:
             tor_df = pd.read_csv(tor_file, delimiter=' ', comment='#', header=None, skipinitialspace=True, low_memory=False,
                                  names=["switch", "totalused", "egressOccupancyLossless", "egressOccupancyLossy",
                                         "ingressPoolOccupancy", "headroomOccupancy", "sharedPoolOccupancy", "time"])
        except pd.errors.EmptyDataError:
             return results
        except Exception as read_e:
             print(f" Error reading TOR file {tor_file}: {read_e}")
             return results

        if tor_df.empty: return results

        # --- Ensure numeric types ---
        for col in ["totalused", "egressOccupancyLossless", "egressOccupancyLossy",
                    "ingressPoolOccupancy", "headroomOccupancy", "sharedPoolOccupancy"]:
            if col in tor_df.columns:
                tor_df[col] = pd.to_numeric(tor_df[col], errors='coerce')


        # --- Percentage Calculations ---
        if buffer_size_bytes > 1:
            # Lossy Egress Pool %
            if "egressOccupancyLossy" in tor_df.columns:
                lossy_buf_pct = (100 * tor_df["egressOccupancyLossy"] / buffer_size_bytes).dropna().tolist()
                if lossy_buf_pct:
                    lossy_buf_pct = [v for v in lossy_buf_pct if np.isfinite(v)] # Filter infinities
                    if lossy_buf_pct:
                         lossy_buf_pct.sort()
                         results["lossy_p99_pct"] = np.percentile(lossy_buf_pct, 99) if len(lossy_buf_pct) >= 100 else np.nan
                         results["lossy_avg_pct"] = np.mean(lossy_buf_pct)

            # Lossless Egress Pool % (Often 0 for Reverie, relevant for SONiC model)
            if "egressOccupancyLossless" in tor_df.columns:
                lossless_buf_pct = (100 * tor_df["egressOccupancyLossless"] / buffer_size_bytes).dropna().tolist()
                if lossless_buf_pct:
                    lossless_buf_pct = [v for v in lossless_buf_pct if np.isfinite(v)]
                    if lossless_buf_pct:
                        lossless_buf_pct.sort()
                        results["lossless_p99_pct"] = np.percentile(lossless_buf_pct, 99) if len(lossless_buf_pct) >= 100 else np.nan
                        results["lossless_avg_pct"] = np.mean(lossless_buf_pct)

            # Total Used Buffer %
            if "totalused" in tor_df.columns:
                total_buf_pct = (100 * tor_df["totalused"] / buffer_size_bytes).dropna().tolist()
                if total_buf_pct:
                    total_buf_pct = [v for v in total_buf_pct if np.isfinite(v)]
                    if total_buf_pct:
                        total_buf_pct.sort()
                        results["total_p99_pct"] = np.percentile(total_buf_pct, 99) if len(total_buf_pct) >= 100 else np.nan
                        results["total_avg_pct"] = np.mean(total_buf_pct)

        # --- Raw Byte Calculations ---
        # Headroom Occupancy (Bytes)
        if "headroomOccupancy" in tor_df.columns:
            headroom_bytes = tor_df["headroomOccupancy"].dropna().tolist()
            if headroom_bytes:
                 headroom_bytes = [v for v in headroom_bytes if np.isfinite(v)]
                 if headroom_bytes:
                     headroom_bytes.sort()
                     results["headroom_p99_bytes"] = np.percentile(headroom_bytes, 99) if len(headroom_bytes) >= 100 else np.nan
                     results["headroom_avg_bytes"] = np.mean(headroom_bytes)

        # Shared Pool Occupancy (Bytes) - Relevant for Reverie model
        if "sharedPoolOccupancy" in tor_df.columns:
            shared_bytes = tor_df["sharedPoolOccupancy"].dropna().tolist()
            if shared_bytes:
                 shared_bytes = [v for v in shared_bytes if np.isfinite(v)]
                 if shared_bytes:
                     shared_bytes.sort()
                     results["shared_p99_bytes"] = np.percentile(shared_bytes, 99) if len(shared_bytes) >= 100 else np.nan
                     results["shared_avg_bytes"] = np.mean(shared_bytes)

        return results
    except Exception as e: print(f"Error analyzing TOR file {tor_file}: {e}"); return results


# --- Experiment Functions (Revised based on shell script cross-checking and using args) ---

# Corresponds to: run-rdma-loads.sh (Varies tcpload)
def experiment_tcp_load_on_rdma_burst(args, results_dir_path):
    """Exp 1: Fixed RDMA burst (2M), vary TCP background load. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 1: TCP Load Impact on Fixed RDMA Burst...")
    headers = ["TCP Load", "Algorithm", "RDMA Incast FCT Slowdown Avg", "PFC Pauses",
               "TCP Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999", "rdmaload": "0"
    }
    for tcpload in SimulationParams.LOADS:
        params["tcpload"] = tcpload
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_incast_stats = analyze_fct_data(fct_file, incast=True, priority=3)
            tcp_short_stats = analyze_fct_data(fct_file, incast=False, priority=1, flowsize_filter=(None, 100000))
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)

            data.append([
                float(tcpload), BufferAlgs.get_names()[alg], rdma_incast_stats["slowdown_avg"],
                pfc_stats["count"], tcp_short_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 1: TCP Load Impact on Fixed RDMA Burst", headers, data, "exp1_tcp_load_on_rdma_burst.csv")

# --- Other Experiment Functions (Need similar modification) ---
# ... (Repeat modification pattern for experiments 2 through 12) ...
# Example for Exp 2:
def experiment_rdma_burst_with_tcp_bg(args, results_dir_path):
    """Exp 2: Fixed TCP background load (0.8), vary RDMA burst size. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 2: RDMA Burst Size Impact with TCP Background...")
    headers = ["RDMA Burst Size", "Algorithm", "RDMA Incast FCT Slowdown Avg", "PFC Pauses",
               "TCP Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "tcpload": "0.8", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999", "rdmaload": "0"
    }
    for rdmaburst in SimulationParams.RDMA_BURST_SIZES_VAR:
        params["rdmaburst"] = rdmaburst
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_incast_stats = analyze_fct_data(fct_file, incast=True, priority=3)
            tcp_short_stats = analyze_fct_data(fct_file, incast=False, priority=1, flowsize_filter=(None, 100000))
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)

            data.append([
                int(rdmaburst), BufferAlgs.get_names()[alg], rdma_incast_stats["slowdown_avg"],
                pfc_stats["count"], tcp_short_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 2: RDMA Burst Size Impact with TCP Background", headers, data, "exp2_rdma_burst_with_tcp_bg.csv")

# --- Add modified functions for Exp 3 - 12 following the pattern ---
def experiment_rdma_load_on_tcp_burst(args, results_dir_path):
    """Exp 3: Fixed TCP burst (1.5M), vary RDMA background load. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 3: RDMA Load Impact on Fixed TCP Burst...")
    headers = ["RDMA Load", "Algorithm", "TCP Incast FCT Slowdown Avg", "PFC Pauses",
               "RDMA Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.INTCC), "tcpcc": args.tcp_cc_code,
        "rdmaburst": "0", "tcpburst": "1500000",
        "egresslossyFrac": "0.8", "gamma": "0.999", "tcpload": "0"
    }
    for rdmaload in SimulationParams.LOADS:
        params["rdmaload"] = rdmaload
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            tcp_incast_stats = analyze_fct_data(fct_file, incast=True, priority=1)
            rdma_short_stats = analyze_fct_data(fct_file, incast=False, priority=3, flowsize_filter=(None, 100000))
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                float(rdmaload), BufferAlgs.get_names()[alg], tcp_incast_stats["slowdown_avg"],
                pfc_stats["count"], rdma_short_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 3: RDMA Load Impact on Fixed TCP Burst", headers, data, "exp3_rdma_load_on_tcp_burst.csv")

def experiment_tcp_burst_with_rdma_bg(args, results_dir_path):
    """Exp 4: Fixed RDMA background load (0.8), vary TCP burst size. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 4: TCP Burst Size Impact with RDMA Background...")
    headers = ["TCP Burst Size", "Algorithm", "TCP Incast FCT Slowdown Avg", "PFC Pauses",
               "RDMA Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.INTCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0.8", "tcpload": "0", "rdmaburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for tcpburst in SimulationParams.TCP_BURST_SIZES_VAR:
        params["tcpburst"] = tcpburst
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            tcp_incast_stats = analyze_fct_data(fct_file, incast=True, priority=1)
            rdma_short_stats = analyze_fct_data(fct_file, incast=False, priority=3, flowsize_filter=(None, 100000))
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                int(tcpburst), BufferAlgs.get_names()[alg], tcp_incast_stats["slowdown_avg"],
                pfc_stats["count"], rdma_short_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 4: TCP Burst Size Impact with RDMA Background", headers, data, "exp4_tcp_burst_with_rdma_bg.csv")

def experiment_gamma_values(args, results_dir_path):
    """Exp 5: Fixed RDMA burst (2M) & RDMA load (0.8), vary gamma for Reverie. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 5: Gamma Parameter Impact experiment...")
    headers = ["Gamma Value", "Algorithm", "RDMA Incast FCT Slowdown Avg", "PFC Pauses",
               "RDMA Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "rdmaload": "0.8", "tcpload": "0"
    }
    alg = str(BufferAlgs.REVERIE)
    params["alg"] = alg
    for gamma in SimulationParams.GAMMA_VALUES:
        params["gamma"] = gamma
        fct_file=get_file_path(args.basePath, "fct", params)
        tor_file=get_file_path(args.basePath, "tor", params)
        pfc_file=get_file_path(args.basePath, "pfc", params)

        rdma_incast_stats = analyze_fct_data(fct_file, incast=True, priority=3)
        rdma_short_stats = analyze_fct_data(fct_file, incast=False, priority=3, flowsize_filter=(None, 100000))
        pfc_stats = analyze_pfc_data(pfc_file)
        buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
        data.append([
            gamma, BufferAlgs.get_names()[alg], rdma_incast_stats["slowdown_avg"],
            pfc_stats["count"], rdma_short_stats["slowdown_p99"],
            buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
            buffer_stats["headroom_p99_bytes"]
        ])
    write_to_csv(results_dir_path, "Exp 5: Impact of Gamma Parameter on Reverie Performance", headers, data, "exp5_gamma_parameter_impact.csv")

def experiment_egress_lossy_fraction(args, results_dir_path):
    """Exp 6: Fixed RDMA burst (2M) & TCP load (0.8), vary egress lossy fraction. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 6: Egress Lossy Fraction Impact experiment...")
    headers = ["Egress Lossy Fraction", "Algorithm", "RDMA Incast FCT Slowdown Avg", "PFC Pauses",
               "TCP Short FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0", "tcpload": "0.8",
        "rdmaburst": "2000000", "tcpburst": "0",
        "gamma": "0.999"
    }
    for lossy_frac in SimulationParams.LOSSY_FRACTIONS:
        params["egresslossyFrac"] = lossy_frac
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_incast_stats = analyze_fct_data(fct_file, incast=True, priority=3)
            tcp_short_stats = analyze_fct_data(fct_file, incast=False, priority=1, flowsize_filter=(None, 100000))
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                float(lossy_frac), BufferAlgs.get_names()[alg], rdma_incast_stats["slowdown_avg"],
                pfc_stats["count"], tcp_short_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 6: Impact of Egress Lossy Fraction", headers, data, "exp6_egress_lossy_fraction_impact.csv")

def experiment_pure_rdma_load(args, results_dir_path):
    """Exp 7: Pure RDMA - Vary RDMA background load, fixed RDMA burst (2M). Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 7: Pure RDMA Load experiment...")
    headers = ["RDMA Load", "Algorithm", "RDMA Background FCT Slowdown Avg", "PFC Pauses",
               "RDMA Background FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "tcpload": "0", "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for rdmaload in SimulationParams.LOADS:
        params["rdmaload"] = rdmaload
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_stats = analyze_fct_data(fct_file, incast=False, priority=3)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                float(rdmaload), BufferAlgs.get_names()[alg], rdma_stats["slowdown_avg"],
                pfc_stats["count"], rdma_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 7: Impact of RDMA Load (Pure RDMA)", headers, data, "exp7_pure_rdma_load_impact.csv")

def experiment_pure_rdma_burst(args, results_dir_path):
    """Exp 8: Pure RDMA - Fixed RDMA background load (0.4), vary RDMA burst size. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 8: Pure RDMA Burst Size experiment...")
    headers = ["RDMA Burst Size", "Algorithm", "RDMA Background FCT Slowdown Avg", "PFC Pauses",
               "RDMA Background FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0.4", "tcpload": "0", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for rdmaburst in SimulationParams.RDMA_BURST_SIZES_VAR:
        params["rdmaburst"] = rdmaburst
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_stats = analyze_fct_data(fct_file, incast=False, priority=3)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                int(rdmaburst), BufferAlgs.get_names()[alg], rdma_stats["slowdown_avg"],
                pfc_stats["count"], rdma_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 8: Impact of RDMA Burst Size (Pure RDMA)", headers, data, "exp8_pure_rdma_burst_impact.csv")

def experiment_pure_rdma_burst_powertcp(args, results_dir_path):
    """Exp 9: Pure RDMA w/ PowerTCP - Fixed RDMA background load (0.4), vary RDMA burst size. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 9: Pure RDMA Burst Size with PowerTCP experiment...")
    headers = ["RDMA Burst Size", "Algorithm", "RDMA Background FCT Slowdown Avg", "PFC Pauses",
               "RDMA Background FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.INTCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0.4", "tcpload": "0", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for rdmaburst in SimulationParams.RDMA_BURST_SIZES_VAR:
        params["rdmaburst"] = rdmaburst
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_stats = analyze_fct_data(fct_file, incast=False, priority=3)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                int(rdmaburst), BufferAlgs.get_names()[alg], rdma_stats["slowdown_avg"],
                pfc_stats["count"], rdma_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 9: Impact of RDMA Burst Size with PowerTCP", headers, data, "exp9_pure_rdma_burst_powertcp_impact.csv")

def experiment_pure_tcp_load(args, results_dir_path):
    """Exp 10: Pure TCP - Vary TCP background load, fixed RDMA burst (2M). Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 10: Pure TCP Load experiment (with RDMA burst background)...")
    headers = ["TCP Load", "Algorithm", "TCP Background FCT Slowdown Avg", "PFC Pauses",
               "TCP Background FCT Slowdown 99%", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0", "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for tcpload in SimulationParams.LOADS:
        params["tcpload"] = tcpload
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            tcp_stats = analyze_fct_data(fct_file, incast=False, priority=1)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                float(tcpload), BufferAlgs.get_names()[alg], tcp_stats["slowdown_avg"],
                pfc_stats["count"], tcp_stats["slowdown_p99"],
                buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 10: Impact of TCP Load (Pure TCP Background + RDMA Burst)", headers, data, "exp10_pure_tcp_load_impact.csv")

def experiment_rdma_tcp_interaction(args, results_dir_path):
    """Exp 11: Interaction - Fixed RDMA load (0.2) & burst (2M), vary TCP background load. Uses args.bufferSizeBytes, args.tcp_cc_code."""
    print("\nRunning Exp 11: RDMA-TCP Interaction experiment...")
    headers = ["TCP Load", "Algorithm", "RDMA Background FCT Slowdown Avg", "TCP Background FCT Slowdown Avg",
               "PFC Pauses", "Lossless Buffer 99% (%)", "Lossy Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0.2", "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    tcp_loads_to_run = ["0.2", "0.4", "0.6"]
    for tcpload in tcp_loads_to_run:
        params["tcpload"] = tcpload
        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_file_path(args.basePath, "fct", params)
            tor_file=get_file_path(args.basePath, "tor", params)
            pfc_file=get_file_path(args.basePath, "pfc", params)

            rdma_stats = analyze_fct_data(fct_file, incast=False, priority=3)
            tcp_stats = analyze_fct_data(fct_file, incast=False, priority=1)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, args.bufferSizeBytes)
            data.append([
                float(tcpload), BufferAlgs.get_names()[alg], rdma_stats["slowdown_avg"], tcp_stats["slowdown_avg"],
                pfc_stats["count"], buffer_stats["lossless_p99_pct"], buffer_stats["lossy_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 11: RDMA-TCP Interaction", headers, data, "exp11_rdma_tcp_interaction.csv")

def experiment_buffer_size(args, results_dir_path):
    """Exp 12: Fixed loads (RDMA=0.2, TCP=0.2), vary buffer size (KB/port/Gbps). Uses args.tcp_cc_code."""
    print("\nRunning Exp 12: Buffer Size Impact experiment...")
    headers = ["Buffer Size (KB/port/Gbps)", "Algorithm", "RDMA Background FCT Slowdown Avg", "TCP Background FCT Slowdown Avg",
               "PFC Pauses", "Total Buffer 99% (%)",
               "Headroom Buffer 99% (Bytes)"]
    data = []
    params = {
        "rdmacc": str(CongestionControl.DCQCNCC), "tcpcc": args.tcp_cc_code,
        "rdmaload": "0.2", "tcpload": "0.2",
        "rdmaburst": "2000000", "tcpburst": "0",
        "egresslossyFrac": "0.8", "gamma": "0.999"
    }
    for buffer_kb_per_port_gbps in SimulationParams.BUFFER_SIZES_KB_PER_PORT_GBPS:
        params["buffer_kb_gbps"] = buffer_kb_per_port_gbps # Use string for filename pattern

        actual_buffer_size_bytes = int(
            args.numPorts *
            SimulationParams.DEFAULT_PORT_SPEED_GBPS *
            1000 *
            float(buffer_kb_per_port_gbps)
        )
        print(f"  Testing Buffer: {buffer_kb_per_port_gbps} KB/port/Gbps -> {actual_buffer_size_bytes} Bytes (using {args.numPorts} ports)")

        for alg in BufferAlgs.get_all():
            params["alg"] = alg
            fct_file=get_buffer_file_path(args.basePath, "fct", params)
            tor_file=get_buffer_file_path(args.basePath, "tor", params)
            pfc_file=get_buffer_file_path(args.basePath, "pfc", params)

            rdma_stats = analyze_fct_data(fct_file, incast=False, priority=3)
            tcp_stats = analyze_fct_data(fct_file, incast=False, priority=1)
            pfc_stats = analyze_pfc_data(pfc_file)
            buffer_stats = analyze_tor_data(tor_file, actual_buffer_size_bytes)
            data.append([
                float(buffer_kb_per_port_gbps), BufferAlgs.get_names()[alg], rdma_stats["slowdown_avg"], tcp_stats["slowdown_avg"],
                pfc_stats["count"], buffer_stats["total_p99_pct"],
                buffer_stats["headroom_p99_bytes"]
            ])
    write_to_csv(results_dir_path, "Exp 12: Impact of Buffer Size", headers, data, "exp12_buffer_size_impact.csv")


# Main Execution Block
def main():
    """Main function to parse arguments and run experiments"""
    parser = argparse.ArgumentParser(description="Run Reverie Simulation Analysis")
    parser.add_argument(
        "--basePath",
        type=str,
        required=True,
        help="Base path containing 'dumps/' subfolder for input and where 'results/' will be created for output."
    )
    parser.add_argument(
        "--numPorts",
        type=int,
        default=SimulationParams.DEFAULT_PORTS,
        help=f"Number of switch ports for default buffer size calculation (default: {SimulationParams.DEFAULT_PORTS})"
    )
    parser.add_argument(
        "--TCPCC",
        type=str,
        default="CUBIC", # Defaulting to CUBIC
        choices=list(CongestionControl.TCP_CC_MAP.keys()),
        help=f"Default TCP Congestion Control algorithm assumed for filename generation (default: CUBIC)"
    )
    parser.add_argument(
        "--experiments",
        nargs='*',
        default=["all"],
        help="Optional list of experiment numbers (1-12) to run. Runs all if not specified."
    )

    args = parser.parse_args()

    # --- Path Setup ---
    if not os.path.isdir(args.basePath):
         print(f"ERROR: Base path '{args.basePath}' does not exist or is not a directory.")
         sys.exit(1)

    # Define and create results directory path
    results_dir_path = os.path.join(args.basePath, "results")
    ensure_directories_exist([results_dir_path]) # Ensure results directory exists


    # Calculate default buffer size in bytes based on numPorts
    args.bufferSizeBytes = int(
            args.numPorts *
            SimulationParams.DEFAULT_PORT_SPEED_GBPS *
            1000 * # KB to Bytes conversion included here
            SimulationParams.DEFAULT_BUFFER_KB_PER_PORT_GBPS
    )

    # Get the integer code for the chosen TCP CC
    try:
        args.tcp_cc_code = CongestionControl.get_tcp_cc_code(args.TCPCC)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Using Base Path: {args.basePath}")
    print(f"Expecting dumps in: {os.path.join(args.basePath, 'dumps')}")
    print(f"Writing results to: {results_dir_path}")
    print(f"Using Num Ports for Default Buffer Calc: {args.numPorts}")
    print(f"Calculated Default Buffer Size: {args.bufferSizeBytes} bytes")
    print(f"Using TCP CC for filename construction: {args.TCPCC} (Code: {args.tcp_cc_code})")

    experiments_to_run = args.experiments
    run_all = "all" in experiments_to_run
    print(f"Running analysis for: {'All' if run_all else experiments_to_run} experiments...")

    # Dictionary mapping corrected experiment numbers/names to functions
    all_experiments = {
        "1": experiment_tcp_load_on_rdma_burst, # run-rdma-loads.sh
        "2": experiment_rdma_burst_with_tcp_bg, # run-rdma-bursts.sh
        "3": experiment_rdma_load_on_tcp_burst, # run-tcp-loads.sh
        "4": experiment_tcp_burst_with_rdma_bg, # run-tcp-bursts.sh
        "5": experiment_gamma_values,           # run-gamma.sh
        "6": experiment_egress_lossy_fraction,  # run-lossyfrac.sh
        "7": experiment_pure_rdma_load,         # lakewood.sh section
        "8": experiment_pure_rdma_burst,        # lakewood.sh section
        "9": experiment_pure_rdma_burst_powertcp,# lakewood.sh section
        "10": experiment_pure_tcp_load,         # lakewood.sh section
        "11": experiment_rdma_tcp_interaction, # loveland.sh section
        "12": experiment_buffer_size           # loveland.sh section
    }

    if run_all:
        for i, (num, exp_func) in enumerate(all_experiments.items(), 1):
            print("-" * 20, f"Running Experiment {num}", "-" * 20)
            try:
                # Pass args AND the results directory path to each function
                exp_func(args, results_dir_path)
            except Exception as e:
                print(f"ERROR running Experiment {num}: {e}")
    else:
        for exp_num in experiments_to_run:
            if exp_num in all_experiments:
                print("-" * 20, f"Running Experiment {exp_num}", "-" * 20)
                try:
                    # Pass args AND the results directory path
                    all_experiments[exp_num](args, results_dir_path)
                except Exception as e:
                    print(f"ERROR running Experiment {exp_num}: {e}")
            else:
                print(f"Warning: Unknown experiment number '{exp_num}'. Skipping.")

    print("\nAnalysis script finished!")

if __name__ == "__main__":
    main()