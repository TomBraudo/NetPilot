import os

def find_netpilot_root():
    """Traverse up the directory tree until we find the 'NetPilot' folder."""
    current_path = os.path.dirname(os.path.abspath(__file__))  # Start from this script's location

    while current_path != os.path.dirname(current_path):  # Stop at the filesystem root
        if os.path.basename(current_path) == "NetPilot":
            return current_path
        current_path = os.path.dirname(current_path)  # Move up one level

    raise FileNotFoundError("NetPilot folder not found in the directory hierarchy.")

def get_data_folder():
    """Returns the full path to the 'data' folder inside NetPilot."""
    netpilot_root = find_netpilot_root()
    data_folder = os.path.join(netpilot_root, "data")
    os.makedirs(data_folder, exist_ok=True)  # Ensure the 'data' folder exists
    return data_folder
