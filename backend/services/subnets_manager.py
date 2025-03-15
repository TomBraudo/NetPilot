import os
import json
from utils.path_utils import get_data_folder

# Define the file path
json_path = os.path.join(get_data_folder(), "Ips_to_scan.json")

def load_ips():
    """Load the IPs from the JSON file, ensuring the structure is valid."""
    if not os.path.exists(json_path):
        return {"subnets": []}

    try:
        with open(json_path, "r") as file:
            data = json.load(file)
            if "subnets" not in data:
                data["subnets"] = []
            return data
    except json.JSONDecodeError:
        return {"subnets": []}

def save_ips(data):
    """Save the updated IP list back to the file."""
    with open(json_path, "w") as file:
        json.dump(data, file, indent=4)

def add_ip(ip):
    """Add an IP address to the list."""
    if not ip:
        return {"error": "Missing IP address"}, 400

    ips_data = load_ips()

    if ip in ips_data["subnets"]:
        return {"error": "IP address already exists"}, 400

    ips_data["subnets"].append(ip)
    save_ips(ips_data)

    return {"message": "IP address added successfully"}, 200

def remove_ip(ip):
    """Remove an IP address from the list."""
    if not ip:
        return {"error": "Missing IP address"}, 400

    ips_data = load_ips()

    if ip not in ips_data["subnets"]:
        return {"error": "IP address not found"}, 404

    ips_data["subnets"].remove(ip)
    save_ips(ips_data)

    return {"message": "IP address removed successfully"}, 200

def clear_ips():
    """Clear all IP addresses from the list."""
    save_ips({"subnets": []})
    return {"message": "All IP addresses cleared successfully"}, 200
