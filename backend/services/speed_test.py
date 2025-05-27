import time
import json
import re
import subprocess
import speedtest
from utils.response_helpers import success, error
from utils.logging_config import get_logger
from utils.ssh_client import ssh_manager

logger = get_logger('services.speed_test')

def run_ookla_speedtest():
    """
    Runs an Ookla speed test on the router and returns the results.
    """
    try:
        # Check if speedtest-cli is installed
        output, error = ssh_manager.execute_command("which speedtest-cli")
        if error:
            # Install speedtest-cli if not present
            output, error = ssh_manager.execute_command("pip3 install speedtest-cli")
            if error:
                raise Exception("Failed to install speedtest-cli")

        # Run speed test with JSON output
        output, error = ssh_manager.execute_command("speedtest-cli --json")
        if error:
            raise Exception(f"Speed test failed: {error}")

        # Parse the JSON output
        result = json.loads(output)
        
        # Format the response
        speed_test_result = {
            "download": round(result["download"] / 1000000, 2),  # Convert to Mbps
            "upload": round(result["upload"] / 1000000, 2),      # Convert to Mbps
            "ping": round(result["ping"], 2),
            "server": {
                "name": result["server"]["name"],
                "country": result["server"]["country"],
                "sponsor": result["server"]["sponsor"]
            },
            "timestamp": result["timestamp"]
        }

        return success(data=speed_test_result)
    except Exception as e:
        logger.error(f"Error running speed test: {str(e)}", exc_info=True)
        raise 