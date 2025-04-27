import os
import pandas as pd
import matplotlib.pyplot as plt

# Add any comparison here
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
    "combined_exp1_tcp_load_on_rdma_burst.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "combined_exp2_rdma_burst_with_tcp_bg.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "combined_exp3_rdma_load_on_tcp_burst.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm"},
    "combined_exp4_tcp_burst_with_rdma_bg.csv": {"x_col": "TCP Burst Size", "algo_col": "Algorithm"},
    "combined_exp5_gamma_parameter_impact.csv": {"x_col": "Gamma Value", "algo_col": "Algorithm"},
    "combined_exp6_egress_lossy_fraction_impact.csv": {"x_col": "Egress Lossy Fraction", "algo_col": "Algorithm"},
    "combined_exp7_pure_rdma_load_impact.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm"},
    "combined_exp8_pure_rdma_burst_impact.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "combined_exp9_pure_rdma_burst_powertcp_impact.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "combined_exp10_pure_tcp_load_impact.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "combined_exp11_rdma_tcp_interaction.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "combined_exp12_buffer_size_impact.csv": {"x_col": "Buffer Size (KB/port/Gbps)", "algo_col": "Algorithm"},
}

color_map = {
    "DT": (0.1, 0.4, 0.8),
    "ABM": (0.8, 0.2, 0.2),
    "Reverie": (0.2, 0.6, 0.2)
}

for comparison_dir, titles in comparison_dirs.items():
    base_dir = os.path.join(os.getcwd(), "Analysis", comparison_dir)
    plots_dir = os.path.join(base_dir, "Graphs")
    os.makedirs(plots_dir, exist_ok=True)

    for filename, config in column_config.items():
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            print(f"Missing file: {path}")
            continue

        df = pd.read_csv(path)
        x_col, algo_col, source_col = config["x_col"], config["algo_col"], "Source"

        metrics = [
            col for col in df.columns
            if col not in [x_col, algo_col, source_col, "CC Algo"] and pd.api.types.is_numeric_dtype(df[col])
        ][:3]

        if not metrics:
            print(f"No numeric metrics found in {path}")
            continue

        sources = sorted(df[source_col].unique())
        if len(sources) != 2:
            print(f"Expected exactly 2 sources, found: {sources}")
            continue

        fig, axes = plt.subplots(3, 2, figsize=(6, 6), dpi=300)

        for row_idx, metric in enumerate(metrics):
            for col_idx, source_value in enumerate(sources):
                ax = axes[row_idx, col_idx]
                df_subset = df[df[source_col] == source_value]

                for algo, subset in df_subset.groupby(algo_col):
                    ax.plot(
                        subset[x_col], subset[metric], label=algo,
                        color=color_map.get(algo, (0.5, 0.5, 0.5)),
                        linestyle='-', marker='o', linewidth=1.8, markersize=5, alpha=0.8
                    )

                ax.set_title(f"{titles[col_idx]} - {metric}", fontsize=10)
                ax.set_xlabel(x_col, fontsize=9)
                ax.set_ylabel(metric, fontsize=9)
                ax.grid(True)
                ax.legend(fontsize=7)

        fig.tight_layout(pad=2.0)
        fig.subplots_adjust(top=0.92)

        output_name = filename.replace('combined_', '').replace('.csv', '_sources_compare.png')
        output_path = os.path.join(plots_dir, output_name)
        fig.savefig(output_path, dpi=500, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved: {output_path}")
