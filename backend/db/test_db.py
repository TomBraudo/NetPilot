import sys
import os

# Ensure the parent directory (backend/) is in the module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.device_repository import get_all_devices


devices = get_all_devices()
for d in devices:
    print(d)
