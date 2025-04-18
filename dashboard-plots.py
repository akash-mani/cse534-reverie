#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverie Dashboard Plotting Script
Reads pre-processed experiment CSV files from an base path
and generates an interactive HTML dashboard plot saved to an output path.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import argparse # For handling command-line arguments
from typing import List, Dict, Optional

# Define algorithm colors and markers (consistent with results.py)
alg_colors = {'DT': 'red', 'ABM': 'blue', 'Reverie': 'green'}
# Use Plotly marker names: https://plotly.com/python/marker-style/
alg_markers = {'DT': 'x', 'ABM': 'triangle-up', 'Reverie': 'circle'}

# --- Data Loading Function ---
def load_data(base_path: str, file_map: Dict[str, str]) -> Dict[str, Optional[pd.DataFrame]]:
    """Loads multiple CSV files from the specified base path."""
    dataframes = {}
    print(f"Loading data from: {base_path}")
    for key, filename in file_map.items():
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                dataframes[key] = pd.read_csv(filepath)
                print(f"  Loaded: {filename}")
            except Exception as e:
                print(f"  Error loading {filename}: {e}")
                dataframes[key] = None
        else:
            print(f"  Warning: File not found - {filename}")
            dataframes[key] = None
    return dataframes

# --- Plotting Helper Function ---
def add_traces(fig: go.Figure, df: Optional[pd.DataFrame], x_col: str, y_col: str,
               row: int, col: int, title: str, xaxis_title: str, yaxis_title: str,
               showlegend: bool = True, add_marker: bool = True):
    """Adds traces for each algorithm to a subplot."""
    # Check if DataFrame is None or essential columns are missing
    if df is None or x_col not in df.columns or y_col not in df.columns or 'Algorithm' not in df.columns:
        print(f" Warning: Skipping plot '{title}' due to missing data or columns '{x_col}', '{y_col}', 'Algorithm'.")
        # Add an annotation indicating missing data
        fig.add_annotation(text="Data Missing", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, row=row, col=col)
        fig.update_xaxes(title_text=xaxis_title, row=row, col=col)
        fig.update_yaxes(title_text=yaxis_title, row=row, col=col)
        return

    algorithms = df['Algorithm'].unique()
    for alg in algorithms:
        if alg not in alg_colors: # Skip if algorithm not recognized
             print(f" Warning: Algorithm '{alg}' not recognized for plotting in '{title}'. Skipping.")
             continue
        # Filter data for the specific algorithm and sort by x-axis value
        alg_df = df[df['Algorithm'] == alg].sort_values(by=x_col)
        # Skip if no data for this algorithm
        if alg_df.empty:
            continue

        marker_symbol = alg_markers.get(alg) if add_marker else None
        fig.add_trace(go.Scatter(x=alg_df[x_col], y=alg_df[y_col],
                                 mode='lines+markers' if add_marker else 'lines',
                                 name=alg,
                                 marker_symbol=marker_symbol,
                                 marker_color=alg_colors.get(alg),
                                 line_color=alg_colors.get(alg),
                                 legendgroup=alg, # Group legends by algorithm
                                 showlegend=showlegend),
                      row=row, col=col)

    # Update axes titles regardless of data presence
    fig.update_xaxes(title_text=xaxis_title, row=row, col=col)
    fig.update_yaxes(title_text=yaxis_title, row=row, col=col)


# --- Main Execution Block ---
def main():
    """Parses arguments, loads data, creates dashboard plot, and saves it."""
    parser = argparse.ArgumentParser(description="Generate Reverie Performance Dashboard Plot")
    parser.add_argument(
        "--basePath",
        type=str,
        required=True,
        help="Path to the directory containing the base exp*.csv files."
    )
    parser.add_argument(
        "--outputFilename",
        type=str,
        default=None,
        help="Name of the output HTML dashboard file (default: reverie_dashboard.html)."
    )

    args = parser.parse_args()

    # Check if base path exists
    if not os.path.exists(args.basePath):  
        print(f"Error: base path '{args.basePath}' does not exist.")
        sys.exit(1)

    # If the user didn’t supply --outputFilename, derive it from basePath:
    if args.outputFilename is None:
        # strip any trailing slash, then take just the final path component
        base_name = os.path.basename(os.path.normpath(args.basePath))
        
    args.outputFilename = f"{base_name}.html"
    basePath = os.path.join(args.basePath, "results/")

    # Define mapping from logical experiment key to expected CSV filename
    file_mapping = {
        "exp1": "exp1_tcp_load_on_rdma_burst.csv",
        "exp2": "exp2_rdma_burst_with_tcp_bg.csv",
        "exp3": "exp3_rdma_load_on_tcp_burst.csv",
        "exp4": "exp4_tcp_burst_with_rdma_bg.csv",
        "exp5": "exp5_gamma_parameter_impact.csv",
        "exp6": "exp6_egress_lossy_fraction_impact.csv",
        "exp7": "exp7_pure_rdma_load_impact.csv",
        "exp8": "exp8_pure_rdma_burst_impact.csv",
        "exp9": "exp9_pure_rdma_burst_powertcp_impact.csv",
        "exp10": "exp10_pure_tcp_load_impact.csv",
        "exp11": "exp11_rdma_tcp_interaction.csv",
        "exp12": "exp12_buffer_size_impact.csv",
    }

    # Load all data from the specified base path
    dfs = load_data(basePath, file_mapping)

    # --- Dashboard Creation ---
    rows = 7
    cols = 2
    subplot_titles = [
        # Row 1: RDMA Incast Performance
        "Exp 1: RDMA Incast FCT vs TCP Load", "Exp 2: RDMA Incast FCT vs RDMA Burst (TCP BG)",
        # Row 2: TCP Incast Performance
        "Exp 3: TCP Incast FCT vs RDMA Load", "Exp 4: TCP Incast FCT vs TCP Burst (RDMA BG)",
        # Row 3: Interaction & Buffer Size
        "Exp 11: RDMA & TCP FCT vs TCP Load", "Exp 12: FCT vs Buffer Size (KB/port/Gbps)",
        # Row 4: PFC & Headroom
        "PFC Pauses vs Load/Burst (Exp 1)", "Headroom Usage (Bytes) vs Load/Burst (Exp 1)",
        # Row 5: Buffer Utilization (%)
        "Lossless Buffer Usage (%) (Exp 1)", "Lossy Buffer Usage (%) (Exp 1)",
        # Row 6: Reverie Tuning & Config
        "Exp 5: Reverie Perf. vs Gamma", "Exp 6: Perf. vs Egress Lossy Fraction",
        # Row 7: Pure Workloads
        "Exp 7: Pure RDMA FCT vs RDMA Load", "Exp 10: Pure TCP FCT vs TCP Load"
    ]

    fig_height = rows * 350
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles, vertical_spacing=0.1) # Increased spacing

    # --- Populate Subplots ---
    # Note: Column names used below must exactly match the headers in your base CSV files.

    # Row 1
    add_traces(fig, dfs.get("exp1"), x_col='TCP Load', y_col='RDMA Incast FCT Slowdown Avg', row=1, col=1, title="Exp 1", xaxis_title="TCP Load (%)", yaxis_title="Avg RDMA Incast FCT Slowdown", showlegend=True)
    add_traces(fig, dfs.get("exp2"), x_col='RDMA Burst Size', y_col='RDMA Incast FCT Slowdown Avg', row=1, col=2, title="Exp 2", xaxis_title="RDMA Burst Size (Bytes)", yaxis_title="Avg RDMA Incast FCT Slowdown", showlegend=False)

    # Row 2
    add_traces(fig, dfs.get("exp3"), x_col='RDMA Load', y_col='TCP Incast FCT Slowdown Avg', row=2, col=1, title="Exp 3", xaxis_title="RDMA Load (%)", yaxis_title="Avg TCP Incast FCT Slowdown", showlegend=False)
    add_traces(fig, dfs.get("exp4"), x_col='TCP Burst Size', y_col='TCP Incast FCT Slowdown Avg', row=2, col=2, title="Exp 4", xaxis_title="TCP Burst Size (Bytes)", yaxis_title="Avg TCP Incast FCT Slowdown", showlegend=False)

    # Row 3
    df_exp11 = dfs.get("exp11")
    if df_exp11 is not None and 'Algorithm' in df_exp11.columns:
        for alg in df_exp11['Algorithm'].unique():
            if alg not in alg_colors: continue
            alg_df = df_exp11[df_exp11['Algorithm'] == alg].sort_values(by='TCP Load')
            if 'RDMA Background FCT Slowdown Avg' in alg_df.columns:
                fig.add_trace(go.Scatter(x=alg_df['TCP Load'], y=alg_df['RDMA Background FCT Slowdown Avg'], mode='lines+markers', name=f"{alg}-RDMA", marker_symbol=alg_markers.get(alg), line=dict(color=alg_colors.get(alg), dash='solid'), legendgroup=alg, showlegend=False), row=3, col=1)
            if 'TCP Background FCT Slowdown Avg' in alg_df.columns:
                fig.add_trace(go.Scatter(x=alg_df['TCP Load'], y=alg_df['TCP Background FCT Slowdown Avg'], mode='lines+markers', name=f"{alg}-TCP", marker_symbol=alg_markers.get(alg), line=dict(color=alg_colors.get(alg), dash='dash'), legendgroup=alg, showlegend=False), row=3, col=1)
    fig.update_xaxes(title_text="TCP Load (%)", row=3, col=1); fig.update_yaxes(title_text="Avg BG FCT Slowdown", row=3, col=1)

    df_exp12 = dfs.get("exp12")
    if df_exp12 is not None and 'Algorithm' in df_exp12.columns:
        for alg in df_exp12['Algorithm'].unique():
             if alg not in alg_colors: continue
             alg_df = df_exp12[df_exp12['Algorithm'] == alg].sort_values(by='Buffer Size (KB/port/Gbps)')
             if 'RDMA Background FCT Slowdown Avg' in alg_df.columns:
                 fig.add_trace(go.Scatter(x=alg_df['Buffer Size (KB/port/Gbps)'], y=alg_df['RDMA Background FCT Slowdown Avg'], mode='lines+markers', name=f"{alg}-RDMA", marker_symbol=alg_markers.get(alg), line=dict(color=alg_colors.get(alg), dash='solid'), legendgroup=alg, showlegend=False), row=3, col=2)
             if 'TCP Background FCT Slowdown Avg' in alg_df.columns:
                 fig.add_trace(go.Scatter(x=alg_df['Buffer Size (KB/port/Gbps)'], y=alg_df['TCP Background FCT Slowdown Avg'], mode='lines+markers', name=f"{alg}-TCP", marker_symbol=alg_markers.get(alg), line=dict(color=alg_colors.get(alg), dash='dash'), legendgroup=alg, showlegend=False), row=3, col=2)
    fig.update_xaxes(title_text="Buffer Size (KB/port/Gbps)", row=3, col=2); fig.update_yaxes(title_text="Avg BG FCT Slowdown", row=3, col=2)

    # Row 4
    add_traces(fig, dfs.get("exp1"), x_col='TCP Load', y_col='PFC Pauses', row=4, col=1, title="Exp 1 PFC", xaxis_title="TCP Load (%)", yaxis_title="PFC Pauses Count", showlegend=False)
    add_traces(fig, dfs.get("exp1"), x_col='TCP Load', y_col='Headroom Buffer 99% (Bytes)', row=4, col=2, title="Exp 1 Headroom", xaxis_title="TCP Load (%)", yaxis_title="p99 Headroom Usage (Bytes)", showlegend=False)

    # Row 5
    add_traces(fig, dfs.get("exp1"), x_col='TCP Load', y_col='Lossless Buffer 99% (%)', row=5, col=1, title="Exp 1 Lossless Buf", xaxis_title="TCP Load (%)", yaxis_title="p99 Lossless Buffer (%)", showlegend=False)
    add_traces(fig, dfs.get("exp1"), x_col='TCP Load', y_col='Lossy Buffer 99% (%)', row=5, col=2, title="Exp 1 Lossy Buf", xaxis_title="TCP Load (%)", yaxis_title="p99 Lossy Buffer (%)", showlegend=False)

    # Row 6
    df_exp5 = dfs.get("exp5")
    if df_exp5 is not None:
        # Ensure Gamma Value is treated appropriately for plotting if it contains non-numeric strings
        df_exp5['Gamma Value Numeric'] = pd.to_numeric(df_exp5['Gamma Value'], errors='coerce')
        if not df_exp5['Gamma Value Numeric'].isnull().all():
             df_exp5 = df_exp5.sort_values(by='Gamma Value Numeric') # Sort if possible

        if 'RDMA Incast FCT Slowdown Avg' in df_exp5.columns:
            fig_gamma_fct = go.Scatter(x=df_exp5['Gamma Value'], y=df_exp5['RDMA Incast FCT Slowdown Avg'], mode='lines+markers', name='Reverie FCT', line_color='green', showlegend=False)
            fig.add_trace(fig_gamma_fct, row=6, col=1)
        if 'PFC Pauses' in df_exp5.columns:
            fig_gamma_pfc = go.Scatter(x=df_exp5['Gamma Value'], y=df_exp5['PFC Pauses'], mode='lines+markers', name='Reverie PFC', line_color='orange', yaxis='y2', showlegend=False)
            fig.add_trace(fig_gamma_pfc, row=6, col=1)
            # Ensure the secondary y-axis is configured correctly for the specific subplot
            fig.update_layout({f'yaxis{fig.layout.yaxis2.plotly_name[5:]}': dict(title='PFC Pauses Count', overlaying='y', side='right', showgrid=False)})

    fig.update_xaxes(title_text="Gamma Value", row=6, col=1, type='category'); fig.update_yaxes(title_text="Avg RDMA Incast FCT Slowdown", row=6, col=1) # Use category for x-axis

    add_traces(fig, dfs.get("exp6"), x_col='Egress Lossy Fraction', y_col='RDMA Incast FCT Slowdown Avg', row=6, col=2, title="Exp 6", xaxis_title="Egress Lossy Fraction", yaxis_title="Avg RDMA Incast FCT Slowdown", showlegend=False)

    # Row 7
    add_traces(fig, dfs.get("exp7"), x_col='RDMA Load', y_col='RDMA Background FCT Slowdown Avg', row=7, col=1, title="Exp 7", xaxis_title="RDMA Load (%)", yaxis_title="Avg RDMA BG FCT Slowdown", showlegend=False)
    add_traces(fig, dfs.get("exp10"), x_col='TCP Load', y_col='TCP Background FCT Slowdown Avg', row=7, col=2, title="Exp 10", xaxis_title="TCP Load (%)", yaxis_title="Avg TCP BG FCT Slowdown", showlegend=False)


    # --- Final Layout and Display ---
    fig.update_layout(
        title_text="Reverie Performance Analysis Dashboard",
        height=fig_height,
        legend_title_text='Algorithm',
        # Removed the invalid property: legend_tracegroup_general_visible=True,
        hovermode='x unified' # Improves hover behavior on plots with multiple lines
    )

    # Construct full output path
    output_file_path = os.path.join(args.basePath, args.outputFilename)

    # Save the figure as an HTML file
    try:
        fig.write_html(output_file_path)
        print(f"\nDashboard saved successfully to {output_file_path}")
    except Exception as e:
        print(f"\nError saving dashboard to {output_file_path}: {e}")

    print("Dashboard script finished.")

if __name__ == "__main__":
    main()