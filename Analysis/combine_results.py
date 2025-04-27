import os
import pandas as pd

# add comparisons here and in make_plots.py

comparisons = [
    ("1-baseline", "7-oversub-fulltop"),
    ("1-baseline", "8-oversub-fulltop-16"),
    ("4-corrected-baseline-smalltop", "5-corrected-dctcp-smalltop"),
    ("4-corrected-baseline-smalltop", "6-oversub-smalltop"),
    ("6-oversub-smalltop", "7-oversub-fulltop"),
    ("7-oversub-fulltop", "8-oversub-fulltop-16"),
    ("1-baseline", "4-corrected-baseline-smalltop"),
]

experiment_files = [
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
    "exp12_buffer_size_impact.csv",
]

def capitalize_folder_name(name):
    return "-".join([part.capitalize() for part in name.split("-")])

for comp in comparisons:
    dir1, dir2 = comp
    base_dirs = [
        os.path.join(os.getcwd(), "data", dir1, "results"),
        os.path.join(os.getcwd(), "data", dir2, "results"),
    ]

    dir1_cap = capitalize_folder_name(dir1)
    dir2_cap = capitalize_folder_name(dir2)

    comparison_dir = f"{dir1_cap}_{dir2_cap}".replace('/', '-')
    plots_dir = os.path.join(os.getcwd(), "Analysis", comparison_dir)
    os.makedirs(plots_dir, exist_ok=True)

    for exp_file in experiment_files:
        output_rows = []

        for base_dir in base_dirs:
            label = os.path.basename(os.path.dirname(base_dir))
            file_path = os.path.join(base_dir, exp_file)

            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)

                    matching_cols = [col for col in df.columns if 'FCT Slowdown Avg' in col]
                    print(f"Matching columns: {matching_cols}")

                    # If found, rename the first match exactly to 'FCT Slowdown Avg'
                    if matching_cols:
                        df.rename(columns={matching_cols[0]: 'FCT Slowdown Avg'}, inplace=True)
                    else:
                        print("No column containing 'FCT Slowdown Avg' was found.")


                    df['Source'] = label
                    output_rows.append(df)
                    print(f"Loaded: {file_path}")
                except Exception as e:
                    print(f"Failed to load {file_path}: {e}")
            else:
                print(f"Missing: {file_path}")

        if output_rows:
            combined_df = pd.concat(output_rows, ignore_index=True)
            combined_csv_path = os.path.join(plots_dir, f"combined_{exp_file}")
            combined_df.to_csv(combined_csv_path, index=False, encoding='utf-8')
            print(f"Saved combined file: {combined_csv_path}")
        else:
            print(f"No data to combine for {exp_file}.")
