
import os
import pandas as pd
import matplotlib.pyplot as plt

# Base directory for CSVs
base_dir = os.path.join(os.getcwd(), "data/7-oversub-fulltop/results")
# base_dir = os.path.join(os.getcwd(), "data/6-baseline-oversub/results")
# base_dir = os.path.join(os.getcwd(), "data/4-corrected-baseline-smalltop/results")
# base_dir = os.path.join(os.getcwd(), "data/5-corrected-dctcp-smalltop/results")

# Color map for algorithms
color_map = {
    "DT": (0.1, 0.4, 0.8),
    "ABM": (0.8, 0.2, 0.2),
    "Reverie": (0.2, 0.6, 0.2)
}

# Config: which x and algorithm columns to use per experiment
experiment_configs = {
    "exp1_tcp_load_on_rdma_burst.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "exp2_rdma_burst_with_tcp_bg.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "exp3_rdma_load_on_tcp_burst.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm"},
    "exp4_tcp_burst_with_rdma_bg.csv": {"x_col": "TCP Burst Size", "algo_col": "Algorithm"},
    "exp5_gamma_parameter_impact.csv": {"x_col": "Gamma Value", "algo_col": "Algorithm"},
    "exp6_egress_lossy_fraction_impact.csv": {"x_col": "Egress Lossy Fraction", "algo_col": "Algorithm"},
    "exp7_pure_rdma_load_impact.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm"},
    "exp8_pure_rdma_burst_impact.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "exp9_pure_rdma_burst_powertcp_impact.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm"},
    "exp10_pure_tcp_load_impact.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "exp11_rdma_tcp_interaction.csv": {"x_col": "TCP Load", "algo_col": "Algorithm"},
    "exp12_buffer_size_impact.csv": {"x_col": "Buffer Size (KB/port/Gbps)", "algo_col": "Algorithm"}
}

# Output directory
plots_dir = os.path.join(base_dir, "individual_plots")
os.makedirs(plots_dir, exist_ok=True)

# Process each experiment
for idx, (filename, config) in enumerate(experiment_configs.items(), start=1):
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"⚠️ File not found: {filename}")
        continue

    df = pd.read_csv(path)
    x_col = config["x_col"]
    algo_col = config["algo_col"]

    metrics = [
        col for col in df.columns
        if col not in [x_col, algo_col] and pd.api.types.is_numeric_dtype(df[col])
    ]

    # Prepare for 3x3 subplot grid
    n = len(metrics)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten() if n > 1 else [axes]

    for i, metric in enumerate(metrics):
        ax = axes[i]
        for algo in df[algo_col].unique():
            subset = df[df[algo_col] == algo]
            ax.plot(
                subset[x_col],
                subset[metric],
                marker='o',
                label=algo,
                linewidth=1.5,
                markersize=4,
                color=color_map.get(algo, (0.5, 0.5, 0.5))
            )
        ax.set_title(f"{metric} vs {x_col}", fontsize=10)
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(metric, fontsize=9)
        ax.grid(True)
        ax.legend(title=algo_col, fontsize=7, title_fontsize=8)

        # Save individual plot
        plt.figure(figsize=(5, 4))
        for algo in df[algo_col].unique():
            subset = df[df[algo_col] == algo]
            plt.plot(
                subset[x_col],
                subset[metric],
                marker='o',
                label=algo,
                linewidth=1.5,
                markersize=4,
                color=color_map.get(algo, (0.5, 0.5, 0.5))
            )
        plt.title(f"{metric} vs {x_col}", fontsize=10)
        plt.xlabel(x_col, fontsize=9)
        plt.ylabel(metric, fontsize=9)
        plt.grid(True)
        plt.legend(title=algo_col, fontsize=7, title_fontsize=8)
        plt.tight_layout()

        safe_metric = metric.replace(" ", "_").replace("/", "_")
        safe_xcol = x_col.replace(" ", "_").replace("/", "_")
        # image_filename = f"Experiment{idx}_{safe_xcol}_vs_{safe_metric}.png"
        # image_path = os.path.join(plots_dir, image_filename)
        # plt.savefig(image_path, dpi=300, bbox_inches='tight')
        # plt.close()
        # print(f"Saved: {image_path}")

    # Clean up unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # Save combined subplot figure
    fig.tight_layout(pad=1.5)
    combined_filename = f"Experiment{idx}_combined.png"
    combined_path = os.path.join(plots_dir, combined_filename)
    fig.savefig(combined_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved combined: {combined_path}")
