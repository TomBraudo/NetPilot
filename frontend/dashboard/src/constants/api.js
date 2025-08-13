// API Configuration
const API_BASE_URL = "http://localhost:5000";

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/login`,
  AUTHORIZE: `${API_BASE_URL}/authorize`,
  LOGOUT: `${API_BASE_URL}/logout`,

  // Health
  HEALTH: `${API_BASE_URL}/api/health`,

  // Devices
  DEVICES: `${API_BASE_URL}/api/devices`,

  // Whitelist (new endpoints)
  WHITELIST: `${API_BASE_URL}/api/whitelist`,

  // Blacklist (new endpoints)
  BLACKLIST: `${API_BASE_URL}/api/blacklist`,

  // Legacy endpoints (for backward compatibility)
  LEGACY_WHITELIST: `${API_BASE_URL}/whitelist`,
  LEGACY_BLACKLIST: `${API_BASE_URL}/blacklist`,

  // Network
  NETWORK: `${API_BASE_URL}/api/network`,
  BANDWIDTH: `${API_BASE_URL}/api/bandwidth`,
  WIFI: `${API_BASE_URL}/api/wifi`,

  // Speed test
  SPEED_TEST: `${API_BASE_URL}/api/speedtest`,

  // Settings
  SETTINGS: `${API_BASE_URL}/api/settings`,


  // 2FA
  TWO_FA: `${API_BASE_URL}/api/2fa`,
  // AGH
  AGH: `${API_BASE_URL}/api/agh`,
  // Monitor (dashboard endpoints)
  MONITOR: {
    CURRENT: `${API_BASE_URL}/api/monitor/current`,
    LAST_WEEK: `${API_BASE_URL}/api/monitor/last-week`,
    LAST_MONTH: `${API_BASE_URL}/api/monitor/last-month`,
    DEVICE: `${API_BASE_URL}/api/monitor/device`,
  },
};

// API Helper functions
export const apiRequest = async (endpoint, options = {}) => {
  const defaultOptions = {
    credentials: "include", // Include cookies for authentication (required for user-based sessions)
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  const finalOptions = {
    ...defaultOptions,
    ...options,
  };

  // Enhanced logging for whitelist add requests only
  if (endpoint.includes("/api/whitelist/add")) {
    console.log("🔍 WHITELIST ADD API REQUEST:");
    console.log("  Endpoint:", endpoint);
    console.log("  Method:", finalOptions.method || "GET");
    console.log("  Credentials:", finalOptions.credentials);
    console.log("  Headers:", finalOptions.headers);
    console.log("  Body:", finalOptions.body || "No body");
    console.log("  Document cookies:", document.cookie);
  }

  const response = await fetch(endpoint, finalOptions);

  if (endpoint.includes("/api/whitelist/add")) {
    console.log("🔍 WHITELIST ADD API RESPONSE:");
    console.log("  Status:", response.status);
    console.log(
      "  Response Headers:",
      Object.fromEntries(response.headers.entries())
    );
  }

  if (!response.ok) {
    // Try to extract user-friendly error message from response
    try {
      const errorData = await response.json();
      if (errorData && errorData.message) {
        throw new Error(errorData.message);
      } else if (errorData && errorData.error && errorData.error.message) {
        throw new Error(errorData.error.message);
      }
    } catch (parseError) {
      // If we can't parse the error response, use generic message
      console.warn('Could not parse error response:', parseError);
    }
    
    // Fallback to generic error message
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// Settings API functions
export const settingsAPI = {
  // WiFi name operations
  getWifiName: (routerId) =>
    apiRequest(`${API_ENDPOINTS.SETTINGS}/wifi-name?routerId=${routerId}`),

  setWifiName: (routerId, wifiName) =>
    apiRequest(`${API_ENDPOINTS.SETTINGS}/wifi-name`, {
      method: "POST",
      body: JSON.stringify({
        router_id: routerId,
        wifi_name: wifiName,
      }),
    }),

  // WiFi password operations
  setWifiPassword: (password, routerId = null) =>
    apiRequest(`${API_ENDPOINTS.SETTINGS}/wifi-password`, {
      method: "POST",
      body: JSON.stringify({
        password: password,
        ...(routerId && { router_id: routerId }),
      }),
    }),
};

// Blacklist API functions
export const blacklistAPI = {
  // Get all blacklisted devices
  getAll: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/devices?routerId=${routerId}`),

  // Get specific blacklisted device
  getById: (routerId, id) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/${id}?routerId=${routerId}`),

  // Add device to blacklist
  add: (routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/add?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Update blacklisted device
  update: (routerId, id, deviceData) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/${id}?routerId=${routerId}`, {
      method: "PUT",
      body: JSON.stringify(deviceData),
    }),

  // Remove device from blacklist
  remove: (routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/remove?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Mode operations
  getModeStatus: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/mode?routerId=${routerId}`),

  activateMode: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/mode?routerId=${routerId}`, {
      method: "POST",
    }),

  deactivateMode: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/mode?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Limit rate operations
  getLimitRate: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/limit-rate?routerId=${routerId}`),

  setLimitRate: (routerId, rate) =>
    apiRequest(`${API_ENDPOINTS.BLACKLIST}/limit-rate?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ rate }),
    }),
};

// Whitelist API functions
export const whitelistAPI = {
  // Get all whitelisted devices
  getAll: (routerId) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/devices?routerId=${routerId}`),

  // Get specific whitelisted device
  getById: (routerId, id) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}?routerId=${routerId}`),

  // Add device to whitelist
  add: (routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/add?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Update whitelisted device
  update: (routerId, id, deviceData) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}?routerId=${routerId}`, {
      method: "PUT",
      body: JSON.stringify(deviceData),
    }),

  // Remove device from whitelist
  remove: (routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/remove?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Mode operations
  getModeStatus: (routerId) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`),

  activateMode: (routerId) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`, {
      method: "POST",
    }),

  deactivateMode: (routerId) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Limit rate operations
  getLimitRate: (routerId) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/limit-rate?routerId=${routerId}`),

  setLimitRate: (routerId, rate) =>
    apiRequest(`${API_ENDPOINTS.WHITELIST}/limit-rate?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ rate }),
    }),
};

// Devices API functions
export const devicesAPI = {
  // Get all devices
  getAll: () => apiRequest(API_ENDPOINTS.DEVICES),

  // Get specific device
  getById: (id) => apiRequest(`${API_ENDPOINTS.DEVICES}/${id}`),

  // Add device
  add: (deviceData) =>
    apiRequest(API_ENDPOINTS.DEVICES, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Update device
  update: (id, deviceData) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/${id}`, {
      method: "PUT",
      body: JSON.stringify(deviceData),
    }),

  // Remove device
  remove: (id) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/${id}`, {
      method: "DELETE",
    }),
};

// Network API functions (updated for user-based session management)
export const networkAPI = {
  // Scan network - only requires routerId, sessionId automatically derived from authenticated user
  scan: (routerId) =>
    apiRequest(`${API_ENDPOINTS.NETWORK}/scan?routerId=${routerId}`),

  // Get blocked devices
  getBlocked: (routerId) =>
    apiRequest(`${API_ENDPOINTS.NETWORK}/blocked?routerId=${routerId}`),

  // Block device
  blockDevice: (routerId, ip) =>
    apiRequest(`${API_ENDPOINTS.NETWORK}/block?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ip }),
    }),

  // Unblock device
  unblockDevice: (routerId, ip) =>
    apiRequest(`${API_ENDPOINTS.NETWORK}/unblock?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ip }),
    }),

  // Reset network rules
  resetRules: (routerId) =>
    apiRequest(`${API_ENDPOINTS.NETWORK}/reset?routerId=${routerId}`, {
      method: "POST",
    }),
};

// Session API functions (for commands server session management)
export const sessionAPI = {
  // Start session with commands server - must be called after authentication
  start: (routerId, restart = true) => {
    // Default to restart=true to handle existing sessions
    console.log("📡 sessionAPI.start() called");
    console.log("  📋 Parameters:", { routerId, restart });
    console.log("  🌐 Full URL:", `${API_BASE_URL}/api/session/start`);

    // Note: sessionId is not needed in request body as backend uses user_id as session_id
    // Using restart=true by default to handle cases where session already exists
    const requestBody = { routerId, restart };
    console.log("  📦 Request body:", requestBody);

    return apiRequest(`${API_BASE_URL}/api/session/start`, {
      method: "POST",
      body: JSON.stringify(requestBody),
    })
      .then((response) => {
        console.log("📡 sessionAPI.start() response received:", response);
        return response;
      })
      .catch((error) => {
        console.error("📡 sessionAPI.start() error:", error);
        throw error;
      });
  },

  // End session with commands server
  end: (routerId) => {
    console.log("📡 sessionAPI.end() called");
    console.log("  📋 Parameters:", { routerId });
    console.log("  🌐 Full URL:", `${API_ENDPOINTS.NETWORK}/session/end`);
    console.log("  📦 Request body:", { routerId });

    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/end`, {
      method: "POST",
      body: JSON.stringify({ routerId }),
    })
      .then((response) => {
        console.log("📡 sessionAPI.end() response received:", response);
        return response;
      })
      .catch((error) => {
        console.error("📡 sessionAPI.end() error:", error);
        throw error;
      });
  },

  // Refresh session with commands server
  refresh: () => {
    console.log("📡 sessionAPI.refresh() called");
    console.log("  🌐 Full URL:", `${API_ENDPOINTS.NETWORK}/session/refresh`);

    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/refresh`, {
      method: "POST",
    })
      .then((response) => {
        console.log("📡 sessionAPI.refresh() response received:", response);
        return response;
      })
      .catch((error) => {
        console.error("📡 sessionAPI.refresh() error:", error);
        throw error;
      });
  },

  // Get session status
  status: () => {
    console.log("📡 sessionAPI.status() called");
    console.log("  🌐 Full URL:", `${API_ENDPOINTS.NETWORK}/session/status`);

    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/status`)
      .then((response) => {
        console.log("📡 sessionAPI.status() response received:", response);
        return response;
      })
      .catch((error) => {
        console.error("📡 sessionAPI.status() error:", error);
        throw error;
      });
  },
};

// 2FA API functions
export const twoFAAPI = {
  // Start 2FA setup
  startSetup: () =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/setup/start`, {
      method: "POST",
    }),

  // Verify 2FA setup
  verifySetup: (code, setupToken) =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/setup/verify`, {
      method: "POST",
      body: JSON.stringify({
        code: code,
        setup_token: setupToken,
      }),
    }),

  // Verify 2FA code (during login)
  verify: (code) =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/verify`, {
      method: "POST",
      body: JSON.stringify({
        code: code,
      }),
    }),

  // Get 2FA status
  getStatus: () =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/status`),

  // Disable 2FA
  disable: (confirmationCode) =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/disable`, {
      method: "POST",
      body: JSON.stringify({
        code: confirmationCode,
      }),
    }),

  // Generate new backup codes
  generateBackupCodes: (confirmationCode) =>
    apiRequest(`${API_ENDPOINTS.TWO_FA}/generate-backup-codes`, {
      method: "POST",
      body: JSON.stringify({
        code: confirmationCode,
      }),
    }),
};

// Bandwidth API functions
export const bandwidthAPI = {
  // Group limits
  applyGroupLimits: (routerId, ips, { download_kbytes, upload_kbytes, download_mbps, upload_mbps } = {}) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/limits/group?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ips, download_kbytes, upload_kbytes, download_mbps, upload_mbps }),
    }),

  deleteGroupLimits: (routerId, ips) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/limits/group?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ ips }),
    }),

  // Device limits
  applyDeviceLimit: (routerId, ip, { download_kbytes, upload_kbytes, download_mbps, upload_mbps } = {}) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/limits/device?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ip, download_kbytes, upload_kbytes, download_mbps, upload_mbps }),
    }),

  deleteDeviceLimit: (routerId, ip) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/limits/device?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ ip }),
    }),

  // Global limits
  activateGlobal: (routerId, { download_kbytes, upload_kbytes, lan_cidr } = {}) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/global/activate?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ download_kbytes, upload_kbytes, lan_cidr }),
    }),

  deactivateGlobal: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/global/deactivate?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Global whitelist
  addGlobalWhitelist: (routerId, ips) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/global/whitelist?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ips }),
    }),

  removeGlobalWhitelist: (routerId, ips) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/global/whitelist?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ ips }),
    }),
};

// AGH (AdGuard Home) API functions
export const aghAPI = {
  // Categories
  getCategories: (routerId) =>
    apiRequest(`${API_ENDPOINTS.AGH}/categories?routerId=${routerId}`),

  createCategory: (routerId, category, domains = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/categories?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ category, domains }),
    }),

  getCategoryDomains: (routerId, category) =>
    apiRequest(`${API_ENDPOINTS.AGH}/categories/${encodeURIComponent(category)}/domains?routerId=${routerId}`),

  replaceCategoryDomains: (routerId, category, domains = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/categories/${encodeURIComponent(category)}/domains?routerId=${routerId}`, {
      method: "PUT",
      body: JSON.stringify({ domains }),
    }),

  // Device rules - effective
  getDeviceRules: (routerId, { mac, ip } = {}) => {
    const params = new URLSearchParams({ routerId });
    if (mac) params.append("mac", mac);
    if (ip) params.append("ip", ip);
    return apiRequest(`${API_ENDPOINTS.AGH}/device/rules?${params.toString()}`);
  },

  bulkGetDevicesRules: (routerId, devices = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/devices/rules?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ devices }),
    }),

  // Device rules - set
  setDeviceRules: (routerId, device, categories = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/device/rules?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ device, categories }),
    }),

  setDevicesRules: (routerId, devices = [], categories = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/devices/rules/set?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ devices, categories }),
    }),

  // Device rules - clear
  clearDeviceRules: (routerId, device) =>
    apiRequest(`${API_ENDPOINTS.AGH}/device/rules?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ device }),
    }),

  clearDevicesRules: (routerId, devices = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/devices/rules?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ devices }),
    }),
};
