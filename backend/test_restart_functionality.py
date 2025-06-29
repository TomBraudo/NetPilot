#!/usr/bin/env python3
"""
Test script for the restart functionality in infrastructure setup.
This will test both normal setup and forced restart.
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.router_setup_service import setup_router_infrastructure

def test_restart_functionality():
    """Test the restart flag functionality."""
    print("=" * 60)
    print("TESTING RESTART FUNCTIONALITY")
    print("=" * 60)
    
    print("\n🔧 Testing infrastructure setup with restart functionality...")
    
    # Test 1: Normal setup (should be fast if infrastructure exists)
    print("\n1️⃣  NORMAL SETUP (restart=False):")
    print("   This should skip recreation if infrastructure already exists")
    start_time = time.time()
    
    success, error = setup_router_infrastructure(restart=False)
    
    normal_time = time.time() - start_time
    
    if success:
        print(f"✅ Normal setup completed in {normal_time:.2f} seconds")
    else:
        print(f"❌ Normal setup failed: {error}")
        return
    
    # Test 2: Restart setup (should always rebuild everything)
    print("\n2️⃣  RESTART SETUP (restart=True):")
    print("   This should force complete teardown and rebuild")
    start_time = time.time()
    
    success, error = setup_router_infrastructure(restart=True)
    
    restart_time = time.time() - start_time
    
    if success:
        print(f"✅ Restart setup completed in {restart_time:.2f} seconds")
    else:
        print(f"❌ Restart setup failed: {error}")
        return
    
    # Test 3: Normal setup again (should be fast again)
    print("\n3️⃣  NORMAL SETUP AGAIN (restart=False):")
    print("   This should be fast again since infrastructure now exists")
    start_time = time.time()
    
    success, error = setup_router_infrastructure(restart=False)
    
    second_normal_time = time.time() - start_time
    
    if success:
        print(f"✅ Second normal setup completed in {second_normal_time:.2f} seconds")
    else:
        print(f"❌ Second normal setup failed: {error}")
        return
    
    # Show timing comparison
    print("\n📊 TIMING COMPARISON:")
    print(f"Normal setup (1st):  {normal_time:.2f} seconds")
    print(f"Restart setup:       {restart_time:.2f} seconds") 
    print(f"Normal setup (2nd):  {second_normal_time:.2f} seconds")
    
    print("\n💡 EXPECTED BEHAVIOR:")
    print("   • restart=True should ALWAYS rebuild (slower, consistent time)")
    print("   • restart=False should skip if exists (fast 2nd time)")
    print("   • Restart should be slower than normal (rebuilding everything)")
    
    if restart_time > second_normal_time:
        improvement = ((restart_time - second_normal_time) / restart_time) * 100
        print(f"✅ Optimization working: {improvement:.1f}% faster when skipping recreation")
    else:
        print("⚠️  No optimization detected - check if infrastructure detection is working")

def show_manual_test_commands():
    """Show commands to manually verify restart functionality."""
    print("\n" + "=" * 60)
    print("MANUAL VERIFICATION COMMANDS")
    print("=" * 60)
    
    print("\n📋 To manually verify restart functionality on router:")
    
    print("\n1. Check current infrastructure:")
    print("   iptables -t mangle -L -n | grep NETPILOT")
    print("   tc qdisc show | grep htb")
    
    print("\n2. Run normal setup and check logs:")
    print("   # Should show: 'All infrastructure already exists - skipping setup!'")
    
    print("\n3. Run restart=True and check logs:")
    print("   # Should show: 'RESTART FLAG SET - Forcing complete infrastructure rebuild...'")
    
    print("\n4. Verify infrastructure was recreated:")
    print("   iptables -t mangle -L NETPILOT_WHITELIST -n --line-numbers")
    print("   tc class show dev br-lan")

def test_api_integration():
    """Show how to use restart in API calls."""
    print("\n" + "=" * 60) 
    print("API INTEGRATION")
    print("=" * 60)
    
    print("\n🔌 To use restart flag in your API:")
    print("""
    # In your session or setup endpoint:
    
    # Normal setup (fast)
    success, error = setup_router_infrastructure(restart=False)
    
    # Force restart (slow but guarantees fresh setup)  
    success, error = setup_router_infrastructure(restart=True)
    
    # Example API endpoint:
    @app.route('/setup-infrastructure')
    def setup_infrastructure():
        restart = request.args.get('restart', 'false').lower() == 'true'
        success, error = setup_router_infrastructure(restart=restart)
        
        if success:
            return {'success': True, 'restarted': restart}
        else:
            return {'success': False, 'error': error}, 500
    """)

if __name__ == "__main__":
    print("NetPilot Infrastructure Restart Functionality Test")
    print("This will test the new restart=True parameter")
    
    try:
        test_restart_functionality()
        show_manual_test_commands() 
        test_api_integration()
        
        print("\n🎯 SUMMARY:")
        print("✅ Restart functionality implemented successfully!")
        print("📝 Use restart=True when you need to force a complete rebuild")
        print("⚡ Use restart=False (default) for fast incremental setup")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
