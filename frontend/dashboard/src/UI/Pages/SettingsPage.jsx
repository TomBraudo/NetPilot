import React, { useState, useEffect } from "react";
import { Router, Settings, Edit, Wifi, Save, X, Lock, Eye, EyeOff } from "lucide-react";
import RouterIdPopup from "../../components/RouterIdPopup";
import { useAuth } from "../../context/AuthContext";
import { settingsAPI } from "../../constants/api";

const SettingsPage = () => {
  const [showRouterIdPopup, setShowRouterIdPopup] = useState(false);
  const [wifiName, setWifiName] = useState("");
  const [originalWifiName, setOriginalWifiName] = useState("");
  const [isEditingWifi, setIsEditingWifi] = useState(false);
  const [wifiLoading, setWifiLoading] = useState(true);
  const [wifiError, setWifiError] = useState(null);
  const [isSaving, setIsSaving] = useState(false); // Add saving state
  
  // WiFi Password states
  const [wifiPassword, setWifiPassword] = useState("");
  const [isEditingPassword, setIsEditingPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordError, setPasswordError] = useState(null);
  
  const { routerId, saveRouterIdToBackend } = useAuth();

  // Fetch WiFi name on component mount
  useEffect(() => {
    fetchWifiName();
  }, []);

  const getWifiNameFromStorage = () => {
    try {
      const stored = localStorage.getItem(`wifi_name_${routerId}`);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.warn("Failed to parse WiFi name from localStorage:", error);
      return null;
    }
  };

  const saveWifiNameToStorage = (name) => {
    try {
      localStorage.setItem(`wifi_name_${routerId}`, JSON.stringify(name));
    } catch (error) {
      console.warn("Failed to save WiFi name to localStorage:", error);
    }
  };

  const fetchWifiName = async (forceRefresh = false) => {
    try {
      setWifiLoading(true);
      setWifiError(null);

      // Try to get from localStorage first (unless forcing refresh)
      if (!forceRefresh && routerId) {
        const cachedName = getWifiNameFromStorage();
        if (cachedName) {
          setWifiName(cachedName);
          setOriginalWifiName(cachedName);
          setWifiLoading(false);
          console.log("✅ WiFi name loaded from cache:", cachedName);
          return;
        }
      }

      console.log("📡 Fetching WiFi name from API...");
      const response = await settingsAPI.getWifiName(routerId);

      console.log("📡 WiFi name response:", response);

      if (response.success && response.data) {
        const name = response.data.wifi_name || response.data.ssid || "Unknown";
        setWifiName(name);
        setOriginalWifiName(name);
        
        // Save to localStorage for future use
        if (routerId) {
          saveWifiNameToStorage(name);
        }
        
        console.log("✅ WiFi name loaded from API:", name);
      } else {
        throw new Error(response.message || "Failed to fetch WiFi name");
      }
    } catch (error) {
      console.error("❌ Error fetching WiFi name:", error);
      setWifiError("Failed to load WiFi name");
      setWifiName("Unable to load");
    } finally {
      setWifiLoading(false);
    }
  };

  const handleChangeRouterId = () => {
    setShowRouterIdPopup(true);
  };

  const handleRouterIdConfirm = async (newRouterId) => {
    console.log("Settings page: Router ID change confirmed:", newRouterId);
    setShowRouterIdPopup(false);
  };

  const handleClosePopup = () => {
    setShowRouterIdPopup(false);
  };

  const handleEditWifi = () => {
    setIsEditingWifi(true);
  };

  const handleCancelWifiEdit = () => {
    setWifiName(originalWifiName);
    setIsEditingWifi(false);
  };

  const handleSaveWifiName = async () => {
    console.log("Saving WiFi name:", wifiName);

    // Check if router ID is available
    if (!routerId) {
      console.error("❌ No router ID available");
      setWifiError(
        "Router ID not configured. Please set your router ID first."
      );
      return;
    }

    try {
      setIsSaving(true);
      setWifiError(null);

      console.log("📡 Posting WiFi name update...");
      const response = await settingsAPI.setWifiName(routerId, wifiName);

      console.log("📡 WiFi name update response:", response);

      if (response.success) {
        setOriginalWifiName(wifiName);
        setIsEditingWifi(false);
        
        // Update localStorage with the new name
        if (routerId) {
          saveWifiNameToStorage(wifiName);
        }
        
        console.log("✅ WiFi name saved successfully!");
      } else {
        throw new Error(response.message || "Failed to save WiFi name");
      }
    } catch (error) {
      console.error("❌ Error saving WiFi name:", error);
      setWifiError("Failed to save WiFi name. Please try again.");
      // Revert to original name on error
      setWifiName(originalWifiName);
    } finally {
      setIsSaving(false);
    }
  };

  // WiFi Password functions
  const handleEditPassword = () => {
    setIsEditingPassword(true);
    setPasswordError(null);
    setWifiPassword("");
  };

  const handleCancelPasswordEdit = () => {
    setWifiPassword("");
    setIsEditingPassword(false);
    setPasswordError(null);
    setShowPassword(false);
  };

  const validatePassword = (password) => {
    if (!password || password.trim().length === 0) {
      return "Password cannot be empty";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters long";
    }
    return null;
  };

  const getPasswordStrength = (password) => {
    if (!password) return { strength: "", color: "" };
    
    if (password.length < 8) {
      return { strength: "Weak", color: "text-red-600 dark:text-red-400" };
    }
    
    let score = 0;
    if (password.match(/[a-z]/)) score++;
    if (password.match(/[A-Z]/)) score++;
    if (password.match(/[0-9]/)) score++;
    if (password.match(/[^a-zA-Z0-9]/)) score++;
    
    if (score >= 3 && password.length >= 12) {
      return { strength: "Strong", color: "text-green-600 dark:text-green-400" };
    } else if (score >= 2 && password.length >= 8) {
      return { strength: "Medium", color: "text-yellow-600 dark:text-yellow-400" };
    } else {
      return { strength: "Weak", color: "text-red-600 dark:text-red-400" };
    }
  };

  const handleSavePassword = async () => {
    console.log("Saving WiFi password...");

    const validationError = validatePassword(wifiPassword);
    if (validationError) {
      setPasswordError(validationError);
      return;
    }

    try {
      setPasswordSaving(true);
      setPasswordError(null);

      console.log("📡 Posting WiFi password update...");
      const response = await settingsAPI.setWifiPassword(wifiPassword, routerId);

      console.log("📡 WiFi password update response:", response);

      if (response.success) {
        setIsEditingPassword(false);
        setWifiPassword("");
        setShowPassword(false);
        console.log("✅ WiFi password saved successfully!");
        
        // You could show a success message here
        alert("WiFi password updated successfully!");
      } else {
        throw new Error(response.message || "Failed to save WiFi password");
      }
    } catch (error) {
      console.error("❌ Error saving WiFi password:", error);
      setPasswordError("Failed to save WiFi password. Please try again.");
    } finally {
      setPasswordSaving(false);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Settings
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Configure your application preferences and settings
            </p>
          </div>

          <div className="p-6 space-y-6">
            {/* Router Settings Section */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Router Configuration
              </h2>

              {/* Router ID Setting */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <Router className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        Router ID
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {routerId
                          ? `Current: ${routerId}`
                          : "No router ID configured"}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleChangeRouterId}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    {routerId ? "Change Router ID" : "Set Router ID"}
                  </button>
                </div>

                <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                  💡 Your Router ID connects this dashboard to your NetPilot
                  agent. Changing it will replace your current router
                  connection.
                </div>
              </div>

              {/* WiFi Name Setting */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                      <Wifi className="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        WiFi Network Name (SSID)
                      </h3>
                      {wifiLoading ? (
                        <div className="mt-1">
                          <div className="animate-pulse bg-gray-200 dark:bg-gray-600 h-4 w-32 rounded"></div>
                        </div>
                      ) : wifiError ? (
                        <div className="mt-1">
                          <p className="text-sm text-red-600 dark:text-red-400">
                            {wifiError}
                          </p>
                          <button
                            onClick={() => fetchWifiName(true)}
                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1"
                          >
                            Try again
                          </button>
                        </div>
                      ) : isEditingWifi ? (
                        <div className="mt-2 flex items-center space-x-2">
                          <input
                            type="text"
                            value={wifiName}
                            onChange={(e) => setWifiName(e.target.value)}
                            className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter WiFi name"
                            autoFocus
                            disabled={isSaving}
                          />
                          <button
                            onClick={handleSaveWifiName}
                            disabled={isSaving || !wifiName.trim()}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded transition-colors"
                          >
                            <Save className="w-3 h-3 mr-1" />
                            {isSaving ? "Saving..." : "Save"}
                          </button>
                          <button
                            onClick={handleCancelWifiEdit}
                            disabled={isSaving}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
                          >
                            <X className="w-3 h-3 mr-1" />
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Current: {wifiName}
                        </p>
                      )}
                    </div>
                  </div>

                  {!wifiLoading && !wifiError && !isEditingWifi && (
                    <button
                      onClick={handleEditWifi}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
                    >
                      <Edit className="w-4 h-4 mr-2" />
                      Change Name
                    </button>
                  )}
                </div>

                {!isEditingWifi && (
                  <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                    💡 This is the name that appears when devices search for
                    WiFi networks.
                  </div>
                )}
              </div>
            </div>

            {/* WiFi Password Setting */}
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-orange-200 dark:bg-orange-900/30 rounded-lg">
                    <Lock className="w-5 h-5 text-orange-700 dark:text-orange-300" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                      WiFi Password
                    </h3>
                    {passwordError ? (
                      <div className="mt-1">
                        <p className="text-sm text-red-600 dark:text-red-400">
                          {passwordError}
                        </p>
                      </div>
                    ) : isEditingPassword ? (
                      <div className="mt-2 space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="relative flex-1 max-w-sm">
                            <input
                              type={showPassword ? "text" : "password"}
                              value={wifiPassword}
                              onChange={(e) => setWifiPassword(e.target.value)}
                              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-600 dark:focus:ring-orange-400 focus:border-transparent pr-10"
                              placeholder="Enter new WiFi password"
                              autoFocus
                              disabled={passwordSaving}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              disabled={passwordSaving}
                            >
                              {showPassword ? (
                                <EyeOff className="w-4 h-4" />
                              ) : (
                                <Eye className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                          <button
                            onClick={handleSavePassword}
                            disabled={passwordSaving || !wifiPassword.trim()}
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-orange-700 hover:bg-orange-800 dark:bg-orange-500 dark:hover:bg-orange-600 disabled:bg-gray-400 disabled:cursor-not-allowed rounded transition-colors"
                          >
                            <Save className="w-4 h-4 mr-1" />
                            {passwordSaving ? "Saving..." : "Save"}
                          </button>
                          <button
                            onClick={handleCancelPasswordEdit}
                            disabled={passwordSaving}
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
                          >
                            <X className="w-4 h-4 mr-1" />
                            Cancel
                          </button>
                        </div>
                        {wifiPassword && (
                          <div className="flex items-center space-x-4 text-xs">
                            <div>
                              <span className="text-gray-600 dark:text-gray-400">Strength: </span>
                              <span className={getPasswordStrength(wifiPassword).color}>
                                {getPasswordStrength(wifiPassword).strength}
                              </span>
                            </div>
                            <div className="text-gray-500 dark:text-gray-400">
                              Length: {wifiPassword.length} characters
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        Change your WiFi network password
                      </p>
                    )}
                  </div>
                </div>

                {!isEditingPassword && (
                  <button
                    onClick={handleEditPassword}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-orange-700 dark:text-orange-300 bg-orange-100 dark:bg-orange-900/20 border border-orange-300 dark:border-orange-700 rounded-md hover:bg-orange-200 dark:hover:bg-orange-900/30 transition-colors"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Change Password
                  </button>
                )}
              </div>

              {!isEditingPassword && (
                <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                  💡 Choose a strong password with at least 8 characters, including uppercase, lowercase, numbers, and symbols.
                </div>
              )}
            </div>

            {/* Future Settings Sections */}
            <div className="text-center py-8">
              <div className="text-gray-400 dark:text-gray-500">
                <Settings className="mx-auto h-12 w-12 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  More Settings Coming Soon
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Additional configuration options will be available here in
                  future updates.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Router ID Popup */}
      <RouterIdPopup
        isOpen={showRouterIdPopup}
        onClose={handleClosePopup}
        onConfirm={handleRouterIdConfirm}
        cancelButtonText="Cancel"
        showAsLogout={false}
      />
    </div>
  );
};

export default SettingsPage;
