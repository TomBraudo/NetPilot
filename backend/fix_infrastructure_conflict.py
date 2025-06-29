#!/usr/bin/env python3
"""
NetPilot Infrastructure Conflict Fix

This script disables the persistent infrastructure setup that conflicts 
with the naive mode activation approach.

The issue: setup_router_infrastructure() creates persistent TC and iptables 
chains that conflict with our naive "complete teardown and rebuild" approach.

This script provides solutions to prevent or fix this conflict.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def disable_persistent_infrastructure():
    """
    Modify the session.py file to skip persistent infrastructure setup.
    """
    session_file = "endpoints/session.py"
    
    print("🔧 Disabling persistent infrastructure setup...")
    
    try:
        # Read the current session.py file
        with open(session_file, 'r') as f:
            content = f.read()
        
        # Check if it's already disabled
        if "# DISABLED FOR NAIVE APPROACH" in content:
            print("✅ Persistent infrastructure setup already disabled")
            return True
        
        # Replace the infrastructure setup call
        old_line = "    setup_success, setup_error = setup_router_infrastructure(restart=restart)"
        new_lines = """    # DISABLED FOR NAIVE APPROACH - We use complete teardown/rebuild instead
    # setup_success, setup_error = setup_router_infrastructure(restart=restart)
    setup_success, setup_error = True, None  # Skip persistent infrastructure"""
        
        if old_line in content:
            content = content.replace(old_line, new_lines)
            
            # Write back the modified content
            with open(session_file, 'w') as f:
                f.write(content)
            
            print("✅ Successfully disabled persistent infrastructure setup")
            print("   Modified: endpoints/session.py")
            return True
        else:
            print("❌ Could not find infrastructure setup call in session.py")
            return False
            
    except Exception as e:
        print(f"❌ Error modifying session.py: {e}")
        return False

def create_clean_start_script():
    """
    Create a script that ensures clean router state for naive approach.
    """
    script_content = '''#!/bin/bash
# NetPilot Clean Start Script
# Ensures router is in clean state for naive mode activation

echo "🧹 Starting NetPilot clean router setup..."

# Remove ALL NetPilot iptables rules from ALL chains
echo "Removing iptables rules..."
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D INPUT -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D OUTPUT -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D PREROUTING -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D POSTROUTING -j NETPILOT_WHITELIST 2>/dev/null || true

iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D INPUT -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D OUTPUT -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D PREROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -D POSTROUTING -j NETPILOT_BLACKLIST 2>/dev/null || true

# Flush and remove NetPilot chains
echo "Removing NetPilot chains..."
iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true

# Remove ALL TC rules from ALL interfaces
echo "Removing TC rules from all interfaces..."
for interface in $(ls /sys/class/net/ | grep -v lo); do
    echo "  Cleaning interface: $interface"
    tc qdisc del dev $interface root 2>/dev/null || true
    tc qdisc del dev $interface ingress 2>/dev/null || true
done

# Verify clean state
echo "🔍 Verifying clean state..."
echo "NetPilot chains:"
iptables -t mangle -L | grep -i netpilot || echo "  No NetPilot chains found ✅"

echo "TC rules:"
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc_output=$(tc qdisc show dev $interface | grep -v "qdisc noqueue\\|qdisc pfifo_fast" || echo "clean")
    if [ "$tc_output" = "clean" ]; then
        echo "  $interface: Clean ✅"
    else
        echo "  $interface: $tc_output"
    fi
done

# Test internet connectivity
echo "🌐 Testing internet connectivity..."
if ping -c 3 8.8.8.8 >/dev/null 2>&1; then
    echo "Internet connectivity: Working ✅"
else
    echo "Internet connectivity: Issue ❌"
fi

echo "✅ NetPilot clean start completed!"
echo "Router is now ready for naive mode activation."
'''
    
    script_file = "scripts/netpilot_clean_start.sh"
    
    try:
        # Create scripts directory if it doesn't exist
        os.makedirs("scripts", exist_ok=True)
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make script executable (on Unix systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(script_file, 0o755)
        
        print(f"✅ Created clean start script: {script_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating clean start script: {e}")
        return False

def show_manual_commands():
    """
    Display manual commands to fix infrastructure conflicts.
    """
    print("\n" + "="*60)
    print("📋 MANUAL COMMANDS TO FIX INFRASTRUCTURE CONFLICTS")
    print("="*60)
    
    print("\n🔧 Option 1: Disable Persistent Infrastructure Setup")
    print("Edit endpoints/session.py and comment out this line:")
    print("    # setup_success, setup_error = setup_router_infrastructure(restart=restart)")
    print("    setup_success, setup_error = True, None  # Skip for naive approach")
    
    print("\n🧹 Option 2: Manual Clean Start Commands")
    print("Run these commands on the router to ensure clean state:")
    print("""
# Remove all NetPilot rules
for interface in $(ls /sys/class/net/ | grep -v lo); do
    tc qdisc del dev $interface root 2>/dev/null || true
done

iptables -t mangle -F NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -F NETPILOT_BLACKLIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -X NETPILOT_BLACKLIST 2>/dev/null || true

# Remove all jump rules
iptables -t mangle -D FORWARD -j NETPILOT_WHITELIST 2>/dev/null || true
iptables -t mangle -D FORWARD -j NETPILOT_BLACKLIST 2>/dev/null || true
""")
    
    print("\n✅ After running these, the naive mode activation will work properly")
    print("   because it will start from a completely clean state.")

def main():
    print("NetPilot Infrastructure Conflict Fix Tool")
    print("=========================================")
    print()
    print("The naive mode activation approach conflicts with persistent")
    print("infrastructure setup. This tool helps fix the conflict.")
    print()
    
    # Show manual commands first
    show_manual_commands()
    
    print("\n" + "="*60)
    print("🤖 AUTOMATED FIXES")
    print("="*60)
    
    # Try to disable persistent infrastructure
    success = disable_persistent_infrastructure()
    
    # Create clean start script
    script_success = create_clean_start_script()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if success:
        print("✅ Persistent infrastructure setup disabled")
    else:
        print("❌ Could not disable persistent infrastructure setup")
        print("   Please manually edit endpoints/session.py")
    
    if script_success:
        print("✅ Clean start script created: scripts/netpilot_clean_start.sh")
    else:
        print("❌ Could not create clean start script")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run the manual clean commands on the router")
    print("2. Use the naive mode activation (it will handle everything)")
    print("3. The naive approach will create and tear down infrastructure as needed")
    
    print("\n💡 KEY INSIGHT:")
    print("The naive approach is BETTER because:")
    print("- No persistent state to manage")
    print("- No conflicts between different setups") 
    print("- Always starts from clean slate")
    print("- Easier to debug and maintain")

if __name__ == "__main__":
    main()
