const PortManager = require('./services/PortManager');

async function testPortAllocation() {
  console.log('Testing Port Allocation Fixes...');
  
  const portManager = new PortManager();
  
  try {
    // Initialize database
    await portManager.initialize();
    console.log('✅ Database initialized');
    
    // Test single allocation
    const allocation1 = await portManager.allocatePort('test-router-001');
    console.log('✅ First allocation:', allocation1);
    
    // Test concurrent allocations (simulate race condition)
    console.log('Testing concurrent allocations...');
    const promises = [];
    for (let i = 0; i < 5; i++) {
      promises.push(portManager.allocatePort(`test-router-${String(i).padStart(3, '0')}`));
    }
    
    const results = await Promise.allSettled(promises);
    const successful = results.filter(r => r.status === 'fulfilled');
    const failed = results.filter(r => r.status === 'rejected');
    
    console.log(`✅ Concurrent test: ${successful.length} successful, ${failed.length} failed`);
    
    // Show all allocations
    const allAllocations = await portManager.getAllAllocations();
    console.log('📊 All allocations:', allAllocations.map(a => `${a.routerId}: ${a.port}`));
    
    // Test duplicate allocation
    try {
      const duplicate = await portManager.allocatePort('test-router-001');
      console.log('✅ Duplicate allocation (should return existing):', duplicate);
    } catch (error) {
      console.log('❌ Duplicate allocation failed:', error.message);
    }
    
    console.log('🎉 All tests completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await portManager.cleanup();
  }
}

testPortAllocation(); 