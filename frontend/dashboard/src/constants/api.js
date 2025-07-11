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
  WHITELIST: `${API_BASE_URL}/api/whitelist-new`,
  
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
    credentials: 'include', // Include cookies for authentication
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(endpoint, {
    ...defaultOptions,
    ...options,
  });

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
};

// Whitelist API functions
export const whitelistAPI = {
  // Get all whitelisted devices
  getAll: () => apiRequest(API_ENDPOINTS.WHITELIST),
  
  // Get specific whitelisted device
  getById: (id) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}`),
  
  // Add device to whitelist
  add: (deviceData) => apiRequest(API_ENDPOINTS.WHITELIST, {
    method: 'POST',
    body: JSON.stringify(deviceData),
  }),
  
  // Update whitelisted device
  update: (id, deviceData) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(deviceData),
  }),
  
  // Remove device from whitelist
  remove: (id) => apiRequest(`${API_ENDPOINTS.WHITELIST}/${id}`, {
    method: 'DELETE',
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