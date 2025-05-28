import json
import subprocess
from utils.response_helpers import success
from utils.logging_config import get_logger

logger = get_logger('services.speed_test')

def run_ookla_speedtest():
    """
    Runs an Ookla speed test locally on the backend server and returns the results.
    """
    try:
        logger.info("Running speed test locally using speedtest-cli")
        
        # Run speedtest-cli locally with JSON output
        result = subprocess.run(
            ["speedtest-cli", "--json"],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode != 0:
            logger.error(f"speedtest-cli failed with return code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            raise Exception(f"Speed test failed: {result.stderr}")

        # Parse the JSON output
        speed_data = json.loads(result.stdout)
        
        # Format the response
        speed_test_result = {
            "download": round(speed_data["download"] / 1000000, 2),  # Convert to Mbps
            "upload": round(speed_data["upload"] / 1000000, 2),      # Convert to Mbps
            "ping": round(speed_data["ping"], 2),
            "server": {
                "name": speed_data["server"]["name"],
                "country": speed_data["server"]["country"],
                "sponsor": speed_data["server"]["sponsor"]
            },
            "timestamp": speed_data["timestamp"]
        }

        logger.info(f"Speed test completed: {speed_test_result['download']} Mbps down, {speed_test_result['upload']} Mbps up")
        return success(data=speed_test_result)
        
    except subprocess.TimeoutExpired:
        logger.error("Speed test timed out after 60 seconds")
        raise Exception("Speed test timed out")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse speedtest-cli JSON output: {str(e)}")
        logger.error(f"Raw output: {result.stdout if 'result' in locals() else 'No output'}")
        raise Exception("Failed to parse speed test results")
    except FileNotFoundError:
        logger.error("speedtest-cli not found. Please install it with: pip install speedtest-cli")
        raise Exception("speedtest-cli not installed. Please run: pip install speedtest-cli")
    except Exception as e:
        logger.error(f"Error running speed test: {str(e)}", exc_info=True)
        raise 