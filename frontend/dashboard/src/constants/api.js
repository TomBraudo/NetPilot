// API Configuration
const API_BASE_URL = 'http://localhost:5000';

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
  BLACKLIST: `${API_BASE_URL}/api/blacklist-new`,
  
  // Legacy endpoints (for backward compatibility)
  LEGACY_WHITELIST: `${API_BASE_URL}/whitelist`,
  LEGACY_BLACKLIST: `${API_BASE_URL}/blacklist`,
  
  // Network
  NETWORK: `${API_BASE_URL}/api/network`,
  WIFI: `${API_BASE_URL}/api/wifi`,
  
  // Speed test
  SPEED_TEST: `${API_BASE_URL}/api/speedtest`,
};

// API Helper functions
export const apiRequest = async (endpoint, options = {}) => {
  const defaultOptions = {
    credentials: 'include', // Include cookies for authentication (required for user-based sessions)
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const finalOptions = {
    ...defaultOptions,
    ...options,
  };

  // Enhanced logging for whitelist add requests only
  if (endpoint.includes('/api/whitelist/add')) {
    console.log('🔍 WHITELIST ADD API REQUEST:');
    console.log('  Endpoint:', endpoint);
    console.log('  Method:', finalOptions.method || 'GET');
    console.log('  Credentials:', finalOptions.credentials);
    console.log('  Headers:', finalOptions.headers);
    console.log('  Body:', finalOptions.body || 'No body');
    console.log('  Document cookies:', document.cookie);
  }

  const response = await fetch(endpoint, finalOptions);

  if (endpoint.includes('/api/whitelist/add')) {
    console.log('🔍 WHITELIST ADD API RESPONSE:');
    console.log('  Status:', response.status);
    console.log('  Response Headers:', Object.fromEntries(response.headers.entries()));
  }

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// Blacklist API functions
export const blacklistAPI = {
  // Get all blacklisted devices
  getAll: () => apiRequest(API_ENDPOINTS.BLACKLIST),
  
  // Get specific blacklisted device
  getById: (id) => apiRequest(`${API_ENDPOINTS.BLACKLIST}/${id}`),
  
  // Add device to blacklist
  add: (deviceData) => apiRequest(API_ENDPOINTS.BLACKLIST, {
    method: 'POST',
    body: JSON.stringify(deviceData),
  }),
  
  // Update blacklisted device
  update: (id, deviceData) => apiRequest(`${API_ENDPOINTS.BLACKLIST}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(deviceData),
  }),
  
  // Remove device from blacklist
  remove: (id) => apiRequest(`${API_ENDPOINTS.BLACKLIST}/${id}`, {
    method: 'DELETE',
  }),
  
  // Mode operations
  getModeStatus: () => apiRequest(`${API_ENDPOINTS.LEGACY_BLACKLIST}/mode`),
  
  activateMode: () => apiRequest(`${API_ENDPOINTS.LEGACY_BLACKLIST}/activate`, {
    method: 'POST',
  }),
  
  deactivateMode: () => apiRequest(`${API_ENDPOINTS.LEGACY_BLACKLIST}/deactivate`, {
    method: 'POST',
  }),
  
  // Limit rate operations
  getLimitRate: () => apiRequest(`${API_ENDPOINTS.LEGACY_BLACKLIST}/limit-rate`),
  
  setLimitRate: (rate) => apiRequest(`${API_ENDPOINTS.LEGACY_BLACKLIST}/limit-rate`, {
    method: 'POST',
    body: JSON.stringify({ rate }),
  }),
};

// Whitelist API functions
export const whitelistAPI = {
  // Get all whitelisted devices
  getAll: (routerId) => apiRequest(`${API_ENDPOINTS.WHITELIST}?routerId=${routerId}`),
  
  // Get specific whitelisted device
  getById: (routerId, id) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}?routerId=${routerId}`),
  
  // Add device to whitelist
  add: (routerId, deviceData) => apiRequest(`${API_ENDPOINTS.WHITELIST}/add?routerId=${routerId}`, {
    method: 'POST',
    body: JSON.stringify(deviceData),
  }),
  
  // Update whitelisted device
  update: (routerId, id, deviceData) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}?routerId=${routerId}`, {
    method: 'PUT',
    body: JSON.stringify(deviceData),
  }),
  
  // Remove device from whitelist
  remove: (routerId, id) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}?routerId=${routerId}`, {
    method: 'DELETE',
  }),
  
  // Mode operations
  getModeStatus: (routerId) => apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`),
  
  activateMode: (routerId) => apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`, {
    method: 'POST',
  }),
  
  deactivateMode: (routerId) => apiRequest(`${API_ENDPOINTS.WHITELIST}/mode?routerId=${routerId}`, {
    method: 'DELETE',
  }),
  
  // Limit rate operations
  getLimitRate: (routerId) => apiRequest(`${API_ENDPOINTS.WHITELIST}/limit-rate?routerId=${routerId}`),
  
  setLimitRate: (routerId, rate) => apiRequest(`${API_ENDPOINTS.WHITELIST}/limit-rate?routerId=${routerId}`, {
    method: 'POST',
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
  add: (deviceData) => apiRequest(API_ENDPOINTS.DEVICES, {
    method: 'POST',
    body: JSON.stringify(deviceData),
  }),
  
  // Update device
  update: (id, deviceData) => apiRequest(`${API_ENDPOINTS.DEVICES}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(deviceData),
  }),
  
  // Remove device
  remove: (id) => apiRequest(`${API_ENDPOINTS.DEVICES}/${id}`, {
    method: 'DELETE',
  }),
};

// Network API functions (updated for user-based session management)
export const networkAPI = {
  // Scan network - only requires routerId, sessionId automatically derived from authenticated user
  scan: (routerId) => apiRequest(`${API_ENDPOINTS.NETWORK}/scan?routerId=${routerId}`),
  
  // Get blocked devices
  getBlocked: (routerId) => apiRequest(`${API_ENDPOINTS.NETWORK}/blocked?routerId=${routerId}`),
  
  // Block device
  blockDevice: (routerId, ip) => apiRequest(`${API_ENDPOINTS.NETWORK}/block?routerId=${routerId}`, {
    method: 'POST',
    body: JSON.stringify({ ip }),
  }),
  
  // Unblock device  
  unblockDevice: (routerId, ip) => apiRequest(`${API_ENDPOINTS.NETWORK}/unblock?routerId=${routerId}`, {
    method: 'POST',
    body: JSON.stringify({ ip }),
  }),
  
  // Reset network rules
  resetRules: (routerId) => apiRequest(`${API_ENDPOINTS.NETWORK}/reset?routerId=${routerId}`, {
    method: 'POST',
  }),
};

  // Session API functions (for commands server session management)
  export const sessionAPI = {
    // Start session with commands server - must be called after authentication
    start: (routerId, restart = false) => {
      console.log('📡 sessionAPI.start() called');
      console.log('  📋 Parameters:', { routerId, restart });
      console.log('  🌐 Full URL:', `${API_BASE_URL}/api/session/start`);
      console.log('  📦 Request body:', { routerId, restart });
      
      return apiRequest(`${API_BASE_URL}/api/session/start`, {
        method: 'POST',
        body: JSON.stringify({ routerId, restart }),
      }).then(response => {
        console.log('📡 sessionAPI.start() response received:', response);
        return response;
      }).catch(error => {
        console.error('📡 sessionAPI.start() error:', error);
        throw error;
      });
    },
  
  // End session with commands server
  end: (routerId) => {
    console.log('📡 sessionAPI.end() called');
    console.log('  📋 Parameters:', { routerId });
    console.log('  🌐 Full URL:', `${API_ENDPOINTS.NETWORK}/session/end`);
    console.log('  📦 Request body:', { routerId });
    
    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/end`, {
      method: 'POST', 
      body: JSON.stringify({ routerId }),
    }).then(response => {
      console.log('📡 sessionAPI.end() response received:', response);
      return response;
    }).catch(error => {
      console.error('📡 sessionAPI.end() error:', error);
      throw error;
    });
  },
  
  // Refresh session with commands server
  refresh: () => {
    console.log('📡 sessionAPI.refresh() called');
    console.log('  🌐 Full URL:', `${API_ENDPOINTS.NETWORK}/session/refresh`);
    
    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/refresh`, {
      method: 'POST',
    }).then(response => {
      console.log('📡 sessionAPI.refresh() response received:', response);
      return response;
    }).catch(error => {
      console.error('📡 sessionAPI.refresh() error:', error);
      throw error;
    });
  },
  
  // Get session status
  status: () => {
    console.log('📡 sessionAPI.status() called');
    console.log('  🌐 Full URL:', `${API_ENDPOINTS.NETWORK}/session/status`);
    
    return apiRequest(`${API_ENDPOINTS.NETWORK}/session/status`).then(response => {
      console.log('📡 sessionAPI.status() response received:', response);
      return response;
    }).catch(error => {
      console.error('📡 sessionAPI.status() error:', error);
      throw error;
    });
  },
}; 