import os
import pandas as pd
import matplotlib.pyplot as plt

# Base directory
base_dir = os.path.join(os.getcwd(), "combined_results/smalltop-fulltop")
plots_dir = os.path.join(base_dir, "plots")
os.makedirs(plots_dir, exist_ok=True)

# Color map for algorithms (base part)
color_map = {
    "DT": (0.1, 0.4, 0.8),
    "ABM": (0.8, 0.2, 0.2),
    "Reverie": (0.2, 0.6, 0.2)
}

# Line styles by CC Algo
line_style_map = {
    "TCPCubic": "-",   # Solid line
    "DCTCP": ":"       # Dotted line
}

# Column configs per experiment
column_config = {
    "exp1_tcp_load_on_rdma_burst_combined.csv": {"x_col": "TCP Load", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp2_rdma_burst_with_tcp_bg_combined.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp3_rdma_load_on_tcp_burst_combined.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp4_tcp_burst_with_rdma_bg_combined.csv": {"x_col": "TCP Burst Size", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp5_gamma_parameter_impact_combined.csv": {"x_col": "Gamma Value", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp6_egress_lossy_fraction_impact_combined.csv": {"x_col": "Egress Lossy Fraction", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp7_pure_rdma_load_impact_combined.csv": {"x_col": "RDMA Load", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp8_pure_rdma_burst_impact_combined.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp9_pure_rdma_burst_powertcp_impact_combined.csv": {"x_col": "RDMA Burst Size", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp10_pure_tcp_load_impact_combined.csv": {"x_col": "TCP Load", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp11_rdma_tcp_interaction_combined.csv": {"x_col": "TCP Load", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
    "exp12_buffer_size_impact_combined.csv": {"x_col": "Buffer Size (KB/port/Gbps)", "algo_col": "Algorithm", "tcp_col": "CC Algo"},
}

for filename, config in column_config.items():
    path = os.path.join(base_dir, filename)
    if not os.path.exists(path):
        print(f"⚠️ Missing file: {filename}")
        continue

    df = pd.read_csv(path)
    x_col = config["x_col"]
    algo_col = config["algo_col"]
    tcp_col = config["tcp_col"]

    metrics = [
        col for col in df.columns
        if col not in [x_col, algo_col, tcp_col, "CC Algo"] and pd.api.types.is_numeric_dtype(df[col])
    ]
    if not metrics:
        print(f"⚠️ No numeric metrics in {filename}")
        continue

    n = len(metrics)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten() if n > 1 else [axes]

    for i, metric in enumerate(metrics):
        ax = axes[i]

        for (algo, tcp_variant), subset in df.groupby([algo_col, tcp_col]):
            label = f"{algo}_{tcp_variant}"
            color = color_map.get(algo, (0.5, 0.5, 0.5))
            linestyle = line_style_map.get(tcp_variant, "-")

            ax.plot(
                subset[x_col],
                subset[metric],
                label=label,
                color=color,
                linestyle=linestyle,
                marker='o',
                linewidth=1.5,
                markersize=4,
                alpha=0.3
            )

        ax.set_title(f"{metric} vs {x_col}", fontsize=10)
        ax.set_xlabel(x_col, fontsize=9)
        ax.set_ylabel(metric, fontsize=9)
        ax.grid(True)
        ax.legend(fontsize=7, title_fontsize=8)

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    fig.tight_layout(pad=1.5)
    output_name = filename.replace(".csv", ".png")
    output_path = os.path.join(plots_dir, output_name)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    # print(f"✅ Saved: {output_path}")
