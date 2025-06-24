#!/usr/bin/env node

const TunnelManager = require('./src/modules/TunnelManager');
const PortAllocator = require('./src/modules/PortAllocator');

async function testTunnelSpecific() {
  console.log('🔧 Testing Tunnel Establishment (Focused Test)');
  console.log('='.repeat(50));
  
  const credentials = {
    host: '192.168.1.1',
    username: 'root',
    password: 'YOUR_ROUTER_PASSWORD_HERE',
    port: 22
  };

  const cloudVmConfig = {
    ip: '34.38.207.87',
    user: 'root',
    password: 'YOUR_CLOUD_VM_PASSWORD_HERE'
  };

  let tunnelManager, portAllocator;
  let testPort = null;
  
  try {
    console.log('\n📋 Step 1: Initialize Managers');
    console.log('-'.repeat(30));
    
    tunnelManager = new TunnelManager();
    portAllocator = new PortAllocator();
    
    // Configure cloud VM (only set IP, let it use credentials from .env)
    tunnelManager.setCloudVmIp(cloudVmConfig.ip);
    
    console.log('✅ Managers initialized');
    
    console.log('\n📋 Step 2: Allocate Port');
    console.log('-'.repeat(30));
    
    testPort = await portAllocator.allocatePort();
    console.log(`✅ Port allocated: ${testPort}`);
    
    console.log('\n📋 Step 3: Test Cloud VM Connectivity');
    console.log('-'.repeat(30));
    
    const cloudTest = await tunnelManager.testCloudVmConnectivity();
    console.log('✅ Cloud VM connectivity:', cloudTest.status);
    
    console.log('\n📋 Step 4: Establish Tunnel (with timeout)');
    console.log('-'.repeat(30));
    
    const tunnelPromise = tunnelManager.establishTunnel(credentials, testPort);
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Tunnel establishment timeout (60s)')), 60000);
    });
    
    const result = await Promise.race([tunnelPromise, timeoutPromise]);
    console.log('✅ Tunnel establishment result:', result);
    
    console.log('\n📋 Step 5: Verify Tunnel Status');
    console.log('-'.repeat(30));
    
    const status = await tunnelManager.getTunnelStatus();
    console.log('📊 Tunnel status:', {
      isActive: status.isActive,
      port: status.port,
      routerId: status.routerId,
      hasLogs: status.lastLogs && status.lastLogs.length > 0
    });
    
    if (status.lastLogs && status.lastLogs.length > 0) {
      console.log('\n📋 Recent Tunnel Logs:');
      status.lastLogs.slice(-10).forEach(log => {
        if (log.trim()) console.log(`   ${log.trim()}`);
      });
    }
    
    console.log('\n✅ Tunnel test completed successfully');
    
  } catch (error) {
    console.error('\n❌ Tunnel test failed:', error.message);
    
    // Try to get debug information
    if (tunnelManager && tunnelManager.isConnected) {
      try {
        console.log('\n🔍 Debug Information:');
        
        // Check if tunnel script exists
        const scriptCheck = await tunnelManager.ssh.execCommand('ls -la /root/netpilot_tunnel.sh');
        console.log('   - Tunnel script:', scriptCheck.stdout ? 'EXISTS' : 'MISSING');
        
        // Check tunnel logs
        const tunnelLogs = await tunnelManager.ssh.execCommand('tail -5 /tmp/netpilot_tunnel.log 2>/dev/null || echo "No tunnel logs"');
        console.log('   - Tunnel logs:', tunnelLogs.stdout);
        
        // Check autossh logs
        const autosshLogs = await tunnelManager.ssh.execCommand('tail -5 /tmp/autossh.log 2>/dev/null || echo "No autossh logs"');
        console.log('   - Autossh logs:', autosshLogs.stdout);
        
        // Check running processes
        const processes = await tunnelManager.ssh.execCommand('ps | grep -E "(autossh|ssh)" | grep -v grep');
        console.log('   - SSH processes:', processes.stdout || 'None');
        
      } catch (debugError) {
        console.log('   - Could not get debug info:', debugError.message);
      }
    }
    
  } finally {
    console.log('\n🔧 Cleanup');
    console.log('-'.repeat(30));
    
    // Cleanup
    try {
      if (tunnelManager) {
        await tunnelManager.cleanup();
        console.log('✅ Tunnel manager cleaned up');
      }
    } catch (cleanupError) {
      console.log('⚠️  Tunnel cleanup warning:', cleanupError.message);
    }
    
    try {
      if (portAllocator && testPort) {
        await portAllocator.releasePort();
        console.log('✅ Port released');
      }
    } catch (releaseError) {
      console.log('⚠️  Port release warning:', releaseError.message);
    }
    
    console.log('🏁 Test completed');
  }
}

// Handle process termination gracefully
process.on('SIGINT', () => {
  console.log('\n🛑 Test interrupted by user');
  process.exit(0);
});

// Run the test
testTunnelSpecific().catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
}); 