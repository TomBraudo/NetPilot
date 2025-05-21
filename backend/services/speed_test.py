import time
import json
import re
import subprocess
import speedtest
from utils.response_helpers import success, error

def run_ookla_speedtest():
    """
    Runs a speed test using the Python speedtest-cli package locally.
    
    Returns:
        Dictionary with success/error status and speed test data
    """
    try:
        # Create a Speedtest object
        st = speedtest.Speedtest()
        
        # Get list of servers and pick the best one
        st.get_servers()
        st.get_best_server()
        
        # Run download test
        download_speed = st.download()
        
        # Run upload test
        upload_speed = st.upload()
        
        # Get ping
        ping = st.results.ping
        
        # Get server info
        server = st.results.server
        
        # Get client info
        client = st.results.client
        
        # Format results
        data = {
            "download": round(download_speed / 1000000, 2),  # Convert to Mbps
            "upload": round(upload_speed / 1000000, 2),      # Convert to Mbps
            "ping": ping,
            "server": {
                "name": server.get("name", "Unknown"),
                "location": server.get("country", "Unknown"),
                "sponsor": server.get("sponsor", "Unknown")
            },
            "client": {
                "ip": client.get("ip", "Unknown"),
                "isp": client.get("isp", "Unknown")
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        return success(message="Speed test completed successfully", data=data)
        
    except Exception as e:
        return error(f"Error running speed test: {str(e)}") 