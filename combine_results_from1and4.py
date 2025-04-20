import os
import pandas as pd

# List of CSV filenames
csv_files = [
    "exp1_tcp_load_on_rdma_burst.csv",
    "exp2_rdma_burst_with_tcp_bg.csv",
    "exp3_rdma_load_on_tcp_burst.csv",
    "exp4_tcp_burst_with_rdma_bg.csv",
    "exp5_gamma_parameter_impact.csv",
    "exp6_egress_lossy_fraction_impact.csv",
    "exp7_pure_rdma_load_impact.csv",
    "exp8_pure_rdma_burst_impact.csv",
    "exp9_pure_rdma_burst_powertcp_impact.csv",
    "exp10_pure_tcp_load_impact.csv",
    "exp11_rdma_tcp_interaction.csv",
    "exp12_buffer_size_impact.csv"
]

# Directories
base_dirs = {
    "TCPCubic": os.path.join(os.getcwd(), "data/1-baseline/results"),
    "DCTCP": os.path.join(os.getcwd(), "data/4-corrected-baseline-smalltop/results")
}

# Output directory for combined files
output_dir = os.path.join(os.getcwd(), "combined_results/smalltop-fulltop")
os.makedirs(output_dir, exist_ok=True)

# Process each CSV
for file in csv_files:
    combined_dfs = []
    for tcpcc_algo, base_dir in base_dirs.items():
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df["CC Algo"] = tcpcc_algo
            combined_dfs.append(df)

    # Combine and save if there's data
    if combined_dfs:
        combined_df = pd.concat(combined_dfs, ignore_index=True)

        # Sort by Algorithm and CC Algo
        if "Algorithm" in combined_df.columns:
            combined_df = combined_df.sort_values(by=["Algorithm", "CC Algo"])

        out_filename = file.replace(".csv", "_combined.csv")
        combined_df.to_csv(os.path.join(output_dir, out_filename), index=False)
