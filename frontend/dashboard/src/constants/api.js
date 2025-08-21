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
  // Device Groups
  DEVICE_GROUPS: `${API_BASE_URL}/api/device-groups`,
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

  const response = await fetch(endpoint, finalOptions);

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

 

// Devices API functions
export const devicesAPI = {
  // Get all devices for current user and router
  getDevices: (routerId) => 
    apiRequest(`${API_ENDPOINTS.DEVICES}/?routerId=${routerId}`),

  // Get specific device
  getDevice: (deviceId, routerId) => 
    apiRequest(`${API_ENDPOINTS.DEVICES}/${deviceId}?routerId=${routerId}`),

  // Create or update a single device
  createDevice: (routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify(deviceData),
    }),

  // Update device
  updateDevice: (deviceId, routerId, deviceData) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/${deviceId}?routerId=${routerId}`, {
      method: "PUT",
      body: JSON.stringify(deviceData),
    }),

  // Delete device
  deleteDevice: (deviceId, routerId) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/${deviceId}?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Bulk create devices (for scan)
  bulkCreate: (routerId, devices) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/bulk?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ devices }),
    }),

  // Validate devices exist in database
  validateDevices: (routerId, devices) =>
    apiRequest(`${API_ENDPOINTS.DEVICES}/validate?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ devices }),
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

  deleteCategory: (routerId, category) =>
    apiRequest(`${API_ENDPOINTS.AGH}/categories?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ category }),
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

// Device Groups API functions
export const deviceGroupsAPI = {
  // Get all device groups
  getGroups: (routerId) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups?routerId=${routerId}`),

  // Create a new device group
  createGroup: (routerId, { name, description, device_ids }) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ name, description, device_ids }),
    }),

  // Update a device group
  updateGroup: (routerId, groupId, { name, description }) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups/${groupId}?routerId=${routerId}`, {
      method: "PUT",
      body: JSON.stringify({ name, description }),
    }),

  // Delete a device group
  deleteGroup: (routerId, groupId) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups/${groupId}?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Add device to group
  addDeviceToGroup: (routerId, groupId, deviceId) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups/${groupId}/devices?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId }),
    }),

  // Remove device from group
  removeDeviceFromGroup: (routerId, groupId, deviceId) =>
    apiRequest(`${API_ENDPOINTS.DEVICE_GROUPS}/groups/${groupId}/devices/${deviceId}?routerId=${routerId}`, {
      method: "DELETE",
    }),
};

// Bandwidth Rules API functions (for database persistence)
export const bandwidthRulesAPI = {
  // Get bandwidth rules for a group
  getGroupRules: (routerId, groupId) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/rules/group/${groupId}?routerId=${routerId}`),

  // Get all bandwidth rules for a router
  getAllRules: (routerId) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/rules?routerId=${routerId}`),

  // Create or update bandwidth rules for a group
  setGroupRules: (routerId, groupId, { download_limit_mbps, upload_limit_mbps, description, is_active = true }) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/rules/group/${groupId}?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ 
        download_limit_mbps, 
        upload_limit_mbps, 
        description, 
        is_active 
      }),
    }),

  // Delete bandwidth rules for a group
  deleteGroupRules: (routerId, groupId) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/rules/group/${groupId}?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Apply bandwidth rules to actual devices (legacy function for backward compatibility)
  applyGroupLimits: (routerId, ips, { download_mbps, upload_mbps } = {}) =>
    apiRequest(`${API_ENDPOINTS.BANDWIDTH}/limits/group?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ ips, download_mbps, upload_mbps }),
    }),
};

// Content Control Rules API functions (for database persistence)
export const contentControlRulesAPI = {
  // Get content control rules for a group
  getGroupRules: (routerId, groupId) =>
    apiRequest(`${API_ENDPOINTS.AGH}/rules/group/${groupId}?routerId=${routerId}`),

  // Get all content control rules for a router
  getAllRules: (routerId) =>
    apiRequest(`${API_ENDPOINTS.AGH}/rules?routerId=${routerId}`),

  // Create or update content control rules for a group
  setGroupRules: (routerId, groupId, { blocked_categories, description, is_active = true }) =>
    apiRequest(`${API_ENDPOINTS.AGH}/rules/group/${groupId}?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ 
        blocked_categories, 
        description, 
        is_active 
      }),
    }),

  // Delete content control rules for a group
  deleteGroupRules: (routerId, groupId) =>
    apiRequest(`${API_ENDPOINTS.AGH}/rules/group/${groupId}?routerId=${routerId}`, {
      method: "DELETE",
    }),

  // Apply content control rules to actual devices (legacy function for backward compatibility)
  setDevicesRules: (routerId, devices = [], categories = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/devices/rules/set?routerId=${routerId}`, {
      method: "POST",
      body: JSON.stringify({ devices, categories }),
    }),

  // Clear content control rules from actual devices (legacy function for backward compatibility)
  clearDevicesRules: (routerId, devices = []) =>
    apiRequest(`${API_ENDPOINTS.AGH}/devices/rules?routerId=${routerId}`, {
      method: "DELETE",
      body: JSON.stringify({ devices }),
    }),
};

// Scheduled Tasks API functions
export const scheduledTasksAPI = {
  // Get available tasks that can be scheduled
  getAvailableTasks: () =>
    apiRequest(`${API_BASE_URL}/api/scheduled-tasks/available-tasks`),
  
  // Create scheduled task
  createTask: (routerId, service, task, params, hour, minute, days_of_week = null, task_type = 'fixed', interval_minutes = null) =>
    apiRequest(`${API_BASE_URL}/api/scheduled-tasks`, {
      method: "POST",
      body: JSON.stringify({ 
        router_id: routerId, 
        service, 
        task, 
        params, 
        hour, 
        minute, 
        days_of_week,
        task_type,
        interval_minutes
      }),
    }),
  
  // List tasks for a router
  listTasks: (routerId, enabled = null) => {
    const params = new URLSearchParams({ router_id: routerId });
    if (enabled !== null) params.append("enabled", enabled.toString());
    return apiRequest(`${API_BASE_URL}/api/scheduled-tasks?${params.toString()}`);
  },
  
  // Delete task
  deleteTask: (taskId) =>
    apiRequest(`${API_BASE_URL}/api/scheduled-tasks/${taskId}`, {
      method: "DELETE",
    }),
  
  // Toggle task enabled/disabled
  toggleTask: (taskId, enabled) =>
    apiRequest(`${API_BASE_URL}/api/scheduled-tasks/${taskId}/toggle`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
    }),
  
  // Update task timing only
  updateTiming: (taskId, hour, minute, days_of_week) =>
    apiRequest(`${API_BASE_URL}/api/scheduled-tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({ hour, minute, days_of_week }),
    }),
};
