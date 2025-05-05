def create_emergency_access():
    """
    Create emergency SSH access to reset everything if locked out.
    """
    try:
        # Create a recovery script that resets all filtering
        recovery_script = """#!/bin/sh
        # Emergency recovery script
        # Resets all network filtering to allow all connections
        
        # Reset wireless settings
        for iface in $(uci show wireless | grep wifi-iface | cut -d. -f2 | cut -d= -f1); do
            uci set wireless.$iface.macfilter='disable'
            uci delete wireless.$iface.maclist
        done
        
        # Commit and apply
        uci commit wireless
        wifi reload
        
        # Reset firewall rules
        iptables -F FORWARD
        iptables -P FORWARD ACCEPT
        
        echo "Emergency recovery complete - all filtering reset"
        """
        
        # Write recovery script
        recovery_file = "/root/netpilot_recovery.sh"
        cmd = f"echo '{recovery_script}' > {recovery_file} && chmod +x {recovery_file}"
        ssh_manager.execute_command(cmd)
        
        # Create a simple way to run it via SSH
        return success(f"Emergency recovery script created at {recovery_file}")
    except Exception as e:
        logger.error(f"Error creating emergency access: {str(e)}")
        return error(f"Error creating emergency access: {str(e)}") 