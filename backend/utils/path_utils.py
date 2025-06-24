import os
import sys

def find_netpilot_root():
    """Finds the 'NetPilot' root directory, whether running as a script or a PyInstaller executable."""

    # If running as a PyInstaller EXE, use the location of the .exe
    if getattr(sys, 'frozen', False):  # Detects if running from a PyInstaller bundle
        base_path = os.path.dirname(sys.executable)  # Location of server.exe
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Normal script execution

    # Search upwards until we find 'NetPilot'
    while base_path != os.path.dirname(base_path):  # Stop at root directory
        if os.path.basename(base_path) == "NetPilot":
            return base_path
        base_path = os.path.dirname(base_path)  # Move up one level

    raise FileNotFoundError("NetPilot folder not found in the directory hierarchy.")

def get_data_folder():
    """Returns the full path to the 'data' folder inside NetPilot."""
    netpilot_root = find_netpilot_root()
    data_folder = os.path.join(netpilot_root, "data")
    os.makedirs(data_folder, exist_ok=True)  # Ensure the 'data' folder exists
    return data_folder
