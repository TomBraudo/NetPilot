import React, { useState, useEffect } from "react";
import { Router, Settings, Edit, Wifi, Save, X } from "lucide-react";
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
  const { routerId, saveRouterIdToBackend } = useAuth();

  // Fetch WiFi name on component mount
  useEffect(() => {
    fetchWifiName();
  }, []);

  const fetchWifiName = async () => {
    try {
      setWifiLoading(true);
      setWifiError(null);

      console.log("📡 Fetching WiFi name...");
      const response = await settingsAPI.getWifiName(routerId);

      console.log("📡 WiFi name response:", response);

      if (response.success && response.data) {
        const name = response.data.wifi_name || response.data.ssid || "Unknown";
        setWifiName(name);
        setOriginalWifiName(name);
        console.log("✅ WiFi name loaded:", name);
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
                            onClick={fetchWifiName}
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
