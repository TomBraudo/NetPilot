#!/usr/bin/env python3
"""
Test script for the optimized infrastructure setup.
This will show how much faster the setup is when infrastructure already exists.
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.router_setup_service import setup_router_infrastructure

def test_infrastructure_setup_speed():
    """Test the speed of infrastructure setup."""
    print("=" * 60)
    print("TESTING OPTIMIZED INFRASTRUCTURE SETUP")
    print("=" * 60)
    
    print("\n🔍 Testing infrastructure setup speed...")
    print("This will show how fast setup is when infrastructure already exists.")
    
    # First run - might create infrastructure
    print("\n1️⃣  FIRST RUN (may create infrastructure):")
    start_time = time.time()
    
    success, error = setup_router_infrastructure()
    
    first_run_time = time.time() - start_time
    
    if success:
        print(f"✅ Setup completed successfully in {first_run_time:.2f} seconds")
    else:
        print(f"❌ Setup failed: {error}")
        return
    
    # Second run - should be much faster (infrastructure exists)
    print("\n2️⃣  SECOND RUN (infrastructure should already exist):")
    start_time = time.time()
    
    success, error = setup_router_infrastructure()
    
    second_run_time = time.time() - start_time
    
    if success:
        print(f"✅ Setup completed successfully in {second_run_time:.2f} seconds")
    else:
        print(f"❌ Setup failed: {error}")
        return
    
    # Show speed improvement
    print("\n📊 PERFORMANCE COMPARISON:")
    print(f"First run:  {first_run_time:.2f} seconds")
    print(f"Second run: {second_run_time:.2f} seconds")
    
    if second_run_time < first_run_time:
        improvement = ((first_run_time - second_run_time) / first_run_time) * 100
        print(f"🚀 Speed improvement: {improvement:.1f}% faster!")
        print(f"⚡ Time saved: {first_run_time - second_run_time:.2f} seconds")
    else:
        print("⚠️  No significant speed improvement detected")
    
    print("\n💡 The second run should be much faster because:")
    print("   • TC infrastructure already exists → skipped")
    print("   • Iptables chains already exist → skipped") 
    print("   • Only device population happens → fast")
    
def show_infrastructure_status():
    """Show current infrastructure status on router."""
    print("\n" + "=" * 60)
    print("INFRASTRUCTURE STATUS CHECK")
    print("=" * 60)
    
    print("\nTo see what infrastructure exists on your router, run these commands:")
    print("\n📋 Check TC on all interfaces:")
    print("for iface in $(ls /sys/class/net/ | grep -v lo); do")
    print("    echo \"=== $iface ===\"")
    print("    tc qdisc show dev $iface 2>/dev/null || echo \"No TC\"")
    print("done")
    
    print("\n📋 Check iptables chains:")
    print("iptables -t mangle -L NETPILOT_WHITELIST -n 2>/dev/null || echo \"Whitelist chain missing\"")
    print("iptables -t mangle -L NETPILOT_BLACKLIST -n 2>/dev/null || echo \"Blacklist chain missing\"")
    
    print("\n📋 Check active rules:")
    print("iptables -t mangle -L PREROUTING -n")
    print("iptables -t mangle -L FORWARD -n")

if __name__ == "__main__":
    print("NetPilot Optimized Infrastructure Setup Test")
    print("This will test the new fast infrastructure setup that skips recreation.")
    
    try:
        test_infrastructure_setup_speed()
        show_infrastructure_status()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Test whitelist mode activation (should now be faster)")
        print("2. Check that your device gets unlimited speed")
        print("3. Monitor logs to see the optimization working")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
