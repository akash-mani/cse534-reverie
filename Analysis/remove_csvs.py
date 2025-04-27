import os

# Set up the base directory
base_dir = os.path.join(os.getcwd(), "Analysis")

# Check if the directory exists
if os.path.exists(base_dir):
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(base_dir):
        for filename in files:
            if filename.endswith(".csv"):
                file_path = os.path.join(root, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
else:
    print(f"Directory not found: {base_dir}")
