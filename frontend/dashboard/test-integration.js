#!/usr/bin/env node
/**
 * Frontend-Backend Integration Test
 *
 * This script tests the connection between the frontend dashboard API utilities
 * and the backend monitor endpoints to ensure proper data flow.
 */

const fetch = require("node-fetch");

// Mock the frontend API configuration
const API_BASE_URL = "http://localhost:5000";
const API_ENDPOINTS = {
  MONITOR: {
    CURRENT: `${API_BASE_URL}/api/monitor/current`,
    LAST_WEEK: `${API_BASE_URL}/api/monitor/last-week`,
    LAST_MONTH: `${API_BASE_URL}/api/monitor/last-month`,
    DEVICE: `${API_BASE_URL}/api/monitor/device`,
  },
};

/**
 * Test the monitor data fetching logic (simulates frontend behavior)
 */
async function testMonitorDataFetch(timeRange = "day", macAddress = "all") {
  try {
    let url;

    // If specific MAC address is requested, use device endpoint
    if (macAddress !== "all") {
      let period;
      switch (timeRange) {
        case "day":
          period = "current";
          break;
        case "week":
          period = "week";
          break;
        case "month":
          period = "month";
          break;
        default:
          period = "current";
      }
      url = `${API_ENDPOINTS.MONITOR.DEVICE}/${macAddress}?period=${period}`;
    } else {
      // Use appropriate bulk endpoint based on time range
      switch (timeRange) {
        case "day":
          url = API_ENDPOINTS.MONITOR.CURRENT;
          break;
        case "week":
          url = API_ENDPOINTS.MONITOR.LAST_WEEK;
          break;
        case "month":
          url = API_ENDPOINTS.MONITOR.LAST_MONTH;
          break;
        default:
          url = API_ENDPOINTS.MONITOR.CURRENT;
      }
    }

    console.log(`📡 Testing URL: ${url}`);

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-Dev-Mode": "true",
      },
    });

    console.log(`📊 Response Status: ${response.status}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    // Handle both single device and multiple devices responses
    if (macAddress !== "all") {
      // Single device response - wrap in array for consistency
      return {
        data: result.data ? [result.data] : [],
        metadata: result.metadata || {},
      };
    } else {
      // Multiple devices response
      return {
        data: result.data || [],
        metadata: result.metadata || {},
      };
    }
  } catch (error) {
    console.error(`❌ Failed to fetch monitor data: ${error.message}`);
    return null;
  }
}

/**
 * Run comprehensive tests
 */
async function runIntegrationTests() {
  console.log("🧪 Frontend-Backend Integration Tests");
  console.log("=" * 50);

  const testCases = [
    {
      timeRange: "day",
      macAddress: "all",
      description: "Current day - all devices",
    },
    {
      timeRange: "week",
      macAddress: "all",
      description: "Last week - all devices",
    },
    {
      timeRange: "month",
      macAddress: "all",
      description: "Last month - all devices",
    },
    {
      timeRange: "day",
      macAddress: "AA:BB:CC:DD:EE:FF",
      description: "Current day - specific device",
    },
    {
      timeRange: "week",
      macAddress: "AA:BB:CC:DD:EE:FF",
      description: "Last week - specific device",
    },
    {
      timeRange: "month",
      macAddress: "AA:BB:CC:DD:EE:FF",
      description: "Last month - specific device",
    },
  ];

  for (const testCase of testCases) {
    console.log(`\n🔍 Testing: ${testCase.description}`);
    console.log(`   Time Range: ${testCase.timeRange}`);
    console.log(`   MAC Filter: ${testCase.macAddress}`);

    const result = await testMonitorDataFetch(
      testCase.timeRange,
      testCase.macAddress
    );

    if (result) {
      console.log(`   ✅ Success!`);
      console.log(`   📊 Data Count: ${result.data ? result.data.length : 0}`);
      console.log(
        `   📋 Metadata: ${JSON.stringify(result.metadata, null, 2)}`
      );
    } else {
      console.log(`   ❌ Failed!`);
    }
  }

  console.log("\n" + "=" * 50);
  console.log("🏁 Integration tests completed!");
}

// Run the tests
if (require.main === module) {
  runIntegrationTests().catch(console.error);
}

module.exports = { testMonitorDataFetch, runIntegrationTests };
