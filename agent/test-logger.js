#!/usr/bin/env node

/**
 * Logger Test Script
 * Tests the custom logger to verify proper line formatting and no race conditions
 */

const logger = require('./src/utils/Logger');

console.log('=== Testing Clean Logger ===');

// Test different log levels and categories
logger.main('NetPilot Agent starting up...');
logger.config('Configuration loaded successfully');
logger.tunnel('Tunnel established on port 2215');
logger.router('Router configured successfully');
logger.port('Port 2215 allocated');
logger.status('Status API server started');
logger.error('Test error message');
logger.warn('Test warning message');
logger.info('Test info message');
logger.debug('Test debug message');

// Test generic log method
logger.log('INFO', 'CUSTOM', 'Custom category test message');

console.log('Logger test completed. Check logs directory for clean output.');

// Wait for queue to process
setTimeout(() => {
  console.log('Log files should now be written.');
  process.exit(0);
}, 500); 