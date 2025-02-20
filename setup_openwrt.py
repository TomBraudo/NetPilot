import subprocess

def setup_openwrt():
    """
    Runs the OpenWrt setup script to install required packages and configure the router.
    """
    try:
        print("[INFO] Running setup_openwrt.sh...")
        
        # Run the shell script
        process = subprocess.run(["bash", "setup_openwrt.sh"], capture_output=True, text=True)

        # Print output
        print("[INFO] Script Output:\n", process.stdout)

        # Check for errors
        if process.returncode != 0:
            print("[ERROR] Script failed:\n", process.stderr)
            return {"error": "Setup script encountered an error."}

        return {"success": "OpenWrt setup completed successfully."}

    except Exception as e:
        return {"error": str(e)}

# Run the setup when executed
if __name__ == "__main__":
    result = setup_openwrt()
    print(result)
