// API utility functions for the dashboard

import { API_ENDPOINTS, apiRequest } from "../constants/api.js";

/**
 * Fetch monitor data from the backend based on time range
 * @param {string} timeRange - 'day', 'week', or 'month'
 * @param {string} macAddress - specific MAC address or 'all'
 * @returns {Promise<Object>} Monitor data with devices and metadata
 */
export const fetchMonitorData = async (
  timeRange = "day",
  macAddress = "all"
) => {
  // Get routerId from localStorage like other API calls
  const routerId = localStorage.getItem("routerId");

  console.log("🚀 [fetchMonitorData] Starting fetch operation", {
    timeRange,
    macAddress,
    routerId,
    timestamp: new Date().toISOString(),
  });

  if (!routerId) {
    console.warn("⚠️ [fetchMonitorData] No routerId found in localStorage");
  }

  try {
    let url;

    // If specific MAC address is requested, use device endpoint
    if (macAddress !== "all") {
      console.log("📱 [fetchMonitorData] Fetching data for specific device", {
        macAddress,
        routerId,
      });

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
      if (routerId) {
        url += `&routerId=${routerId}`;
      }
      console.log("🔗 [fetchMonitorData] Device endpoint URL constructed", {
        url,
        period,
        routerId,
      });
    } else {
      console.log("📊 [fetchMonitorData] Fetching bulk data for all devices", {
        timeRange,
        routerId,
      });

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

      // Add routerId as query parameter for bulk endpoints
      if (routerId) {
        url += `?routerId=${routerId}`;
      }

      console.log("🔗 [fetchMonitorData] Bulk endpoint URL constructed", {
        url,
        timeRange,
        routerId,
      });
    }

    console.log("📡 [fetchMonitorData] Making API request with credentials", {
      url,
      method: "GET",
      credentials: "include",
      willIncludeCookies: true,
    });

    const result = await apiRequest(url);

    console.log("✅ [fetchMonitorData] API response received and parsed", {
      dataLength: result.data ? result.data.length : 0,
      hasMetadata: !!result.metadata,
      resultKeys: Object.keys(result),
    });

    // Handle both single device and multiple devices responses
    if (macAddress !== "all") {
      console.log("🔄 [fetchMonitorData] Processing single device response", {
        macAddress,
        hasData: !!result.data,
        dataStructure: result.data ? Object.keys(result.data) : null,
      });

      // Single device response - wrap in array for consistency
      const processedData = {
        data: result.data ? [result.data] : [],
        metadata: result.metadata || {},
      };

      console.log(
        "✅ [fetchMonitorData] Single device data processed successfully",
        {
          deviceCount: processedData.data.length,
          metadata: processedData.metadata,
        }
      );

      return processedData;
    } else {
      console.log(
        "🔄 [fetchMonitorData] Processing multiple devices response",
        {
          deviceCount: result.data ? result.data.length : 0,
          hasMetadata: !!result.metadata,
        }
      );

      // Multiple devices response
      const processedData = {
        data: result.data || [],
        metadata: result.metadata || {},
      };

      console.log(
        "✅ [fetchMonitorData] Multiple devices data processed successfully",
        {
          deviceCount: processedData.data.length,
          metadata: processedData.metadata,
        }
      );

      return processedData;
    }
  } catch (error) {
    console.error(
      "💥 [fetchMonitorData] Error occurred during fetch operation",
      {
        error: error.message,
        stack: error.stack,
        timeRange,
        macAddress,
        routerId,
        timestamp: new Date().toISOString(),
      }
    );

    console.warn("🔄 [fetchMonitorData] Falling back to mock data");
    const mockData = getMockData();

    console.log("📦 [fetchMonitorData] Mock data returned", {
      deviceCount: mockData.data.length,
      isMockData: true,
      originalRouterId: routerId,
    });

    // Return mock data as fallback
    return mockData;
  }
};

/**
 * Legacy function name for backward compatibility
 * @deprecated Use fetchMonitorData instead
 */
export const fetchNetworkData = fetchMonitorData;

/**
 * Fetch devices list for filtering
 * @returns {Promise<Array>} List of devices with IP and MAC
 */
export const fetchDevices = async () => {
  // Get routerId from localStorage like other API calls
  const routerId = localStorage.getItem("routerId");

  console.log("🔍 [fetchDevices] Starting devices fetch operation", {
    endpoint: API_ENDPOINTS.DEVICES,
    routerId,
    timestamp: new Date().toISOString(),
  });

  if (!routerId) {
    console.warn("⚠️ [fetchDevices] No routerId found in localStorage");
  }

  try {
    console.log(
      "📡 [fetchDevices] Making API request to devices endpoint with credentials"
    );

    // Add routerId as query parameter if available
    let url = API_ENDPOINTS.DEVICES;
    if (routerId) {
      url += `?routerId=${routerId}`;
    }

    console.log("🔗 [fetchDevices] Final URL constructed", { url, routerId });

    const data = await apiRequest(url);

    console.log("✅ [fetchDevices] Devices data parsed successfully", {
      deviceCount: Array.isArray(data) ? data.length : 0,
      dataType: typeof data,
      isArray: Array.isArray(data),
      routerId,
    });

    return data;
  } catch (error) {
    console.error("💥 [fetchDevices] Error occurred during devices fetch", {
      error: error.message,
      stack: error.stack,
      endpoint: API_ENDPOINTS.DEVICES,
      routerId,
      timestamp: new Date().toISOString(),
    });

    console.warn("🔄 [fetchDevices] Returning empty array as fallback");
    return [];
  }
};

/**
 * Mock data for development and fallback
 * @returns {Object} Mock network data
 */
export const getMockData = () => {
  console.log(
    "🎭 [getMockData] Generating mock data for fallback/development",
    {
      timestamp: new Date().toISOString(),
      purpose: "fallback or development",
    }
  );

  const mockData = {
    data: [
      {
        connections: 210541,
        download: 10969.18,
        ip: "192.168.1.122",
        mac: "d8:bb:c1:47:3a:43",
        unit: "MB",
        upload: 1681.12,
        device_name: "Tom's iPhone",
        hostname: "iPhone.local",
        manufacturer: "Apple Inc."
      },
      {
        connections: 89234,
        download: 5234.67,
        ip: "192.168.1.105",
        mac: "a2:45:d6:78:9b:12",
        unit: "MB",
        upload: 897.34,
        device_name: "Work Laptop",
        hostname: "DESKTOP-ABC123",
        manufacturer: "Dell Inc."
      },
      {
        connections: 45678,
        download: 3456.89,
        ip: "192.168.1.134",
        mac: "f1:23:45:67:89:ab",
        unit: "MB",
        upload: 567.23,
        device_name: "Smart TV",
        hostname: "Samsung-TV",
        manufacturer: "Samsung Electronics"
      },
      {
        connections: 156789,
        download: 8765.43,
        ip: "192.168.1.178",
        mac: "c9:87:65:43:21:ef",
        unit: "MB",
        upload: 1234.56,
        device_name: "Gaming Console",
        hostname: "PS5",
        manufacturer: "Sony Interactive Entertainment"
      },
      {
        connections: 78901,
        download: 2345.67,
        ip: "192.168.1.198",
        mac: "b8:76:54:32:10:cd",
        unit: "MB",
        upload: 432.1,
        device_name: "Security Camera",
        hostname: "camera-01",
        manufacturer: "Ring LLC"
      },
      {
        connections: 125000,
        download: 2048.00,
        ip: "192.168.1.200",
        mac: "aa:bb:cc:dd:ee:ff",
        unit: "MB",
        upload: 512.00,
        device_name: "Media Server",
        hostname: "NAS-01",
        manufacturer: "Synology"
      },
      {
        connections: 25,
        download: 5.00,
        ip: "192.168.1.201",
        mac: "ff:ee:dd:cc:bb:aa",
        unit: "MB",
        upload: 2.00,
        device_name: "Low Traffic Device",
        hostname: "test-device",
        manufacturer: "Unknown"
      }
    ],
    metadata: {
      executionTime: 0.72,
      routerId: "xxx",
      sessionId: "xxx",
      timestamp: new Date().toISOString(),
    },
  };

  console.log("📦 [getMockData] Mock data generated", {
    deviceCount: mockData.data.length,
    totalDownload: mockData.data.reduce(
      (sum, device) => sum + device.download,
      0
    ),
    totalUpload: mockData.data.reduce((sum, device) => sum + device.upload, 0),
    totalConnections: mockData.data.reduce(
      (sum, device) => sum + device.connections,
      0
    ),
  });

  return mockData;
};

/**
 * Format bytes to appropriate unit (B, KB, MB, GB)
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size with unit
 */
export const formatBytes = (bytes) => {
  console.log("📏 [formatBytes] Formatting bytes", { inputBytes: bytes });

  if (bytes === 0) {
    console.log("📏 [formatBytes] Zero bytes detected, returning '0 B'");
    return "0 B";
  }

  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const formattedValue = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
  const unit = sizes[i];
  const result = formattedValue + " " + unit;

  console.log("📏 [formatBytes] Bytes formatted", {
    inputBytes: bytes,
    outputValue: formattedValue,
    unit,
    result,
    sizeIndex: i,
  });

  return result;
};

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
export const formatNumber = (num) => {
  console.log("🔢 [formatNumber] Formatting number", { inputNumber: num });

  const result = new Intl.NumberFormat().format(num);

  console.log("🔢 [formatNumber] Number formatted", {
    inputNumber: num,
    formattedResult: result,
  });

  return result;
};

/**
 * Generate time range labels for charts
 * @param {string} timeRange - 'day', 'week', or 'month'
 * @returns {Array<string>} Array of time labels
 */
export const getTimeLabels = (timeRange) => {
  console.log("📅 [getTimeLabels] Generating time labels", { timeRange });

  const now = new Date();
  const labels = [];

  switch (timeRange) {
    case "day":
      console.log("📅 [getTimeLabels] Generating hourly labels for day view");
      for (let i = 23; i >= 0; i--) {
        const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
        labels.push(hour.getHours() + ":00");
      }
      break;
    case "week":
      console.log("📅 [getTimeLabels] Generating daily labels for week view");
      for (let i = 6; i >= 0; i--) {
        const day = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        labels.push(day.toLocaleDateString("en-US", { weekday: "short" }));
      }
      break;
    case "month":
      console.log("📅 [getTimeLabels] Generating daily labels for month view");
      for (let i = 29; i >= 0; i--) {
        const day = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        labels.push(day.getDate().toString());
      }
      break;
    default:
      console.log(
        "📅 [getTimeLabels] Using default labels for unknown time range"
      );
      return ["1h", "2h", "3h", "4h", "5h", "6h"];
  }

  console.log("📅 [getTimeLabels] Time labels generated", {
    timeRange,
    labelCount: labels.length,
    firstLabel: labels[0],
    lastLabel: labels[labels.length - 1],
  });

  return labels;
};

/**
 * Get authentication headers for API requests
 * @deprecated Use the centralized apiRequest function instead
 * @returns {Object} Headers object with authentication
 */
export const getAuthHeaders = () => {
  console.log(
    "⚠️ [getAuthHeaders] DEPRECATED: Use centralized apiRequest instead"
  );

  const headers = {
    "Content-Type": "application/json",
  };

  // Add authentication token if available
  const token = localStorage.getItem("authToken");
  if (token) {
    console.log("🔑 [getAuthHeaders] Adding authentication token to headers");
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    console.log(
      "⚠️ [getAuthHeaders] No authentication token found in localStorage"
    );
  }

  // Note: credentials: "include" should be handled by centralized apiRequest
  console.log("✅ [getAuthHeaders] Headers prepared (DEPRECATED)", {
    hasAuth: !!token,
    headerKeys: Object.keys(headers),
  });

  return headers;
};
