import os
import pandas as pd
import matplotlib.pyplot as plt
import re

# Add comparisons here and in make_plots.py
comparison_dirs = {
    "1-Baseline_7-Oversub-Fulltop": ("4:1 Oversubscription", "8:1 Oversubscription"),
    "1-Baseline_8-Oversub-Fulltop-16": ("Full Topology: 4:1 Oversubscription", "Full Topology: 16:1 Oversubscription"),
    "4-Corrected-Baseline-Smalltop_5-Corrected-Dctcp-Smalltop": ("Smaller Topology: TCP Cubic", "Smaller Topology: DCTCP"),
    "4-Corrected-Baseline-Smalltop_6-Oversub-Smalltop": ("Smaller Topology: 4:1 Oversubscription", "Smaller Topology: 8:1 Oversubscription"),
    "6-Oversub-Smalltop_7-Oversub-Fulltop": ("Smaller Topology (8:1 Oversubscription)", "Larger Topology (8:1 Oversubscription)"),
    "1-Baseline_4-Corrected-Baseline-Smalltop": ("Full Topology(Baseline)", "Smaller Topology(Baseline)"),
    "7-Oversub-Fulltop_8-Oversub-Fulltop-16": ("Full Topology (8:1 Oversubscription)", "Full Topology (16:1 Oversubscription)"),
}

column_config = {
    "combined_exp1_tcp_load_on_rdma_burst.csv": {"X_Var": "TCP Load"},
    "combined_exp2_rdma_burst_with_tcp_bg.csv": {"X_Var": "RDMA Burst Size"},
    "combined_exp3_rdma_load_on_tcp_burst.csv": {"X_Var": "RDMA Load"},
    "combined_exp4_tcp_burst_with_rdma_bg.csv": {"X_Var": "TCP Burst Size"},
    "combined_exp5_gamma_parameter_impact.csv": {"X_Var": "Gamma Value"},
    "combined_exp6_egress_lossy_fraction_impact.csv": {"X_Var": "Egress Lossy Fraction"},
    "combined_exp7_pure_rdma_load_impact.csv": {"X_Var": "RDMA Load"},
    "combined_exp8_pure_rdma_burst_impact.csv": {"X_Var": "RDMA Burst Size"},
    "combined_exp9_pure_rdma_burst_powertcp_impact.csv": {"X_Var": "RDMA Burst Size"},
    "combined_exp10_pure_tcp_load_impact.csv": {"X_Var": "TCP Load"},
    "combined_exp11_rdma_tcp_interaction.csv": {"X_Var": "TCP Load"},
    "combined_exp12_buffer_size_impact.csv": {"X_Var": "Buffer Size (KB/port/Gbps)"},
}

color_map = {
    "DT": (0.1, 0.4, 0.8),
    "ABM": (0.8, 0.2, 0.2),
    "Reverie": (0.2, 0.6, 0.2)
}

for comparison_dir, titles in comparison_dirs.items():
    base_dir = os.path.join(os.getcwd(), "Analysis", comparison_dir)
    plots_dir = os.path.join(base_dir, "InGrid")
    individual_dir = os.path.join(base_dir, "Individual")
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(individual_dir, exist_ok=True)

    for filename, config in column_config.items():
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            print(f"Missing file: {path}")
            continue

        df = pd.read_csv(path)
        X_Var, algo_col, source_col = config["X_Var"], "Algorithm", "Source"

        metrics = [
            col for col in df.columns
            if col not in [X_Var, algo_col, source_col, "CC Algo"] and pd.api.types.is_numeric_dtype(df[col])
        ][:3]

        if not metrics:
            print(f"No numeric metrics found in {path}")
            continue

        sources = sorted(df[source_col].unique())
        if len(sources) != 2:
            print(f"Expected exactly 2 sources, found: {sources}")
            continue

        fig, axes = plt.subplots(3, 2, figsize=(6, 8), dpi=300)

        for row_idx, metric in enumerate(metrics):
            # Find y-axis limits across both sources
            metric_min, metric_max = None, None
            for source_value in sources:
                df_subset = df[df[source_col] == source_value]
                values = df_subset[metric].dropna()
                if not values.empty:
                    min_val, max_val = values.min(), values.max()
                    if metric_min is None or min_val < metric_min:
                        metric_min = min_val
                    if metric_max is None or max_val > metric_max:
                        metric_max = max_val

            # Add margin
            if metric_min is not None and metric_max is not None:
                y_margin = 0.05 * (metric_max - metric_min)
                y_limits = (metric_min - y_margin, metric_max + y_margin)
            else:
                y_limits = None

            for col_idx, source_value in enumerate(sources):
                ax = axes[row_idx, col_idx]
                df_subset = df[df[source_col] == source_value]

                for algo, subset in df_subset.groupby(algo_col):
                    ax.plot(
                        subset[X_Var], subset[metric], label=algo,
                        color=color_map.get(algo, (0.5, 0.5, 0.5)),
                        linestyle='-', marker='o', linewidth=1.2, markersize=3, alpha=0.8
                    )

                title = f"{titles[col_idx]} - {metric}"
                ax.set_title(title, fontsize=8)
                ax.set_xlabel(X_Var, fontsize=7)
                ax.set_ylabel(metric, fontsize=7)
                ax.tick_params(axis='both', which='major', labelsize=6)
                ax.grid(True, linewidth=0.4)
                ax.legend(fontsize=6, loc='best', frameon=False)

                # Apply consistent y-limits
                if y_limits:
                    ax.set_ylim(y_limits)

                # Save individual plots too
                individual_fig, individual_ax = plt.subplots(figsize=(3, 2.5), dpi=300)
                for algo, subset in df_subset.groupby(algo_col):
                    individual_ax.plot(
                        subset[X_Var], subset[metric], label=algo,
                        color=color_map.get(algo, (0.5, 0.5, 0.5)),
                        linestyle='-', marker='o', linewidth=1.2, markersize=3, alpha=0.8
                    )
                individual_ax.set_title(title, fontsize=8)
                individual_ax.set_xlabel(X_Var, fontsize=7)
                individual_ax.set_ylabel(metric, fontsize=7)
                individual_ax.tick_params(axis='both', which='major', labelsize=6)
                individual_ax.grid(True, linewidth=0.4)
                individual_ax.legend(fontsize=6, loc='best', frameon=False)

                # Apply same y-limits to individuals
                if y_limits:
                    individual_ax.set_ylim(y_limits)

                individual_fig.tight_layout()

                clean_title = title.replace(' ', '_').replace(':', '').replace('(', '').replace(')', '').replace('/', '_')
                exp_name = re.search(r'(exp\d+)', filename).group(1)

                exp_folder_name = exp_name.capitalize()
                exp_folder_path = os.path.join(individual_dir, exp_folder_name)
                os.makedirs(exp_folder_path, exist_ok=True)

                individual_filename = f"{exp_name}_{clean_title}.png"
                individual_path = os.path.join(exp_folder_path, individual_filename)

                individual_fig.savefig(individual_path, dpi=500, bbox_inches='tight')
                plt.close(individual_fig)
                print(f"Saved individual plot: {individual_path}")

        fig.tight_layout(pad=3.0)
        fig.subplots_adjust(top=0.93)

        output_name = filename.replace('combined_', '').replace('.csv', '_sources_compare.png')
        output_path = os.path.join(plots_dir, output_name)
        fig.savefig(output_path, dpi=500, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {output_path}")
