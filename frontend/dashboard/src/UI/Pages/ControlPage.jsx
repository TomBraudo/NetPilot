import React, { useState, useEffect } from "react";
import { Trash2, Shield, ShieldOff } from "lucide-react";
import { blacklistAPI, whitelistAPI, API_ENDPOINTS } from "../../constants/api";

export default function ControlPage() {

  const [devices, setDevices] = useState([]);
  const [blacklistedDevices, setBlacklistedDevices] = useState([]);
  const [isWhitelistMode, setIsWhitelistMode] = useState(() => {
    const savedMode = localStorage.getItem("controlPageMode");
    return savedMode ? savedMode === "whitelist" : true;
  });
  const [whitelistModeActive, setWhitelistModeActive] = useState(false);
  const [blacklistModeActive, setBlacklistModeActive] = useState(false);
  const [loadingWhitelistMode, setLoadingWhitelistMode] = useState(false);
  const [loadingBlacklistMode, setLoadingBlacklistMode] = useState(false);
  const [scannedDevices, setScannedDevices] = useState(() => {
    const savedDevices = localStorage.getItem("scannedDevices");
    return savedDevices ? JSON.parse(savedDevices) : [];
  });
  const [download, setDownload] = useState(() => {
    const savedSpeed = localStorage.getItem("speedTestResults");
    return savedSpeed ? JSON.parse(savedSpeed).download : "-";
  });
  const [upload, setUpload] = useState(() => {
    const savedSpeed = localStorage.getItem("speedTestResults");
    return savedSpeed ? JSON.parse(savedSpeed).upload : "-";
  });
  const [isSpeedTesting, setIsSpeedTesting] = useState(false);
  const [whitelistSpeedLimit, setWhitelistSpeedLimit] = useState("");
  const [blacklistSpeedLimit, setBlacklistSpeedLimit] = useState("");

  // Get speed test timestamp
  const getSpeedTestTimestamp = () => {
    const savedSpeed = localStorage.getItem("speedTestResults");
    if (savedSpeed) {
      const data = JSON.parse(savedSpeed);
      const timestamp = new Date(data.timestamp);
      return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return null;
  };

  // These would be fetched from backend in real app
  const activeDevices = scannedDevices.length;
  const whitelisted = devices.length;
  const blacklisted = blacklistedDevices.length;

  // Fetch whitelist data from backend
  const fetchWhitelistData = async () => {
    try {
      const result = await whitelistAPI.getAll();
      if (result.success) {
        setDevices(result.data?.devices || []);
      } else {
        console.error("Failed to fetch whitelist data:", result.error);
      }
    } catch (error) {
      console.error("Error fetching whitelist:", error);
    }
  };

  // Fetch blacklist data from backend
  const fetchBlacklistData = async () => {
    try {
      const result = await blacklistAPI.getAll();
      if (result.success) {
        setBlacklistedDevices(result.data?.devices || []);
      } else {
        console.error("Failed to fetch blacklist data:", result.error);
      }
    } catch (error) {
      console.error("Error fetching blacklist:", error);
    }
  };

  // Fetch whitelist mode status
  const fetchWhitelistMode = async () => {
    try {
      const response = await fetch("http://localhost:5000/whitelist/mode");
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setWhitelistModeActive(result.data?.active || false);
        }
      } else {
        console.error("Failed to fetch whitelist mode:", response.status);
      }
    } catch (error) {
      console.error("Error fetching whitelist mode:", error);
    }
  };

  // Fetch blacklist mode status
  const fetchBlacklistMode = async () => {
    try {
      const response = await fetch("http://localhost:5000/blacklist/mode");
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setBlacklistModeActive(result.data?.active || false);
        }
      } else {
        console.error("Failed to fetch blacklist mode:", response.status);
      }
    } catch (error) {
      console.error("Error fetching blacklist mode:", error);
    }
  };

  // Fetch whitelist speed limit
  const fetchWhitelistSpeedLimit = async () => {
    try {
      const response = await fetch("http://localhost:5000/whitelist/limit-rate", { method: "GET" });
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setWhitelistSpeedLimit(result.data.rate || "");
        }
      } else {
        console.error("Failed to fetch whitelist speed limit:", response.status);
      }
    } catch (error) {
      console.error("Error fetching whitelist speed limit:", error);
    }
  };

  // Fetch blacklist speed limit
  const fetchBlacklistSpeedLimit = async () => {
    try {
      const response = await fetch("http://localhost:5000/blacklist/limit-rate", { method: "GET" });
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setBlacklistSpeedLimit(result.data.rate || "");
        }
      } else {
        console.error("Failed to fetch blacklist speed limit:", response.status);
      }
    } catch (error) {
      console.error("Error fetching blacklist speed limit:", error);
    }
  };

  // Toggle access control mode (unified function)
  const handleToggleAccessControl = async () => {
    // Check if trying to activate a mode while the other mode is active
    const isActivatingWhitelistWhileBlacklistActive = isWhitelistMode && !whitelistModeActive && blacklistModeActive;
    const isActivatingBlacklistWhileWhitelistActive = !isWhitelistMode && !blacklistModeActive && whitelistModeActive;
    
    if (isActivatingWhitelistWhileBlacklistActive || isActivatingBlacklistWhileWhitelistActive) {
      const currentActiveMode = whitelistModeActive ? 'Whitelist' : 'Blacklist';
      const newMode = isWhitelistMode ? 'Whitelist' : 'Blacklist';
      
      const confirmed = window.confirm(
        `${currentActiveMode} mode is currently active. Are you sure you want to switch to ${newMode} mode? This will deactivate ${currentActiveMode} mode.`
      );
      
      if (!confirmed) {
        return; // User cancelled, don't proceed
      }
    }

    if (isWhitelistMode) {
      // Handle whitelist mode
      setLoadingWhitelistMode(true);
      try {
        if (!whitelistModeActive) {
          // If blacklist is active, deactivate it first
          if (blacklistModeActive) {
            console.log("Deactivating blacklist mode before activating whitelist...");
            const deactivateResponse = await fetch("http://localhost:5000/blacklist/deactivate", {
              method: "POST",
              headers: { "Content-Type": "application/json" }
            });
            
            if (!deactivateResponse.ok) {
              throw new Error(`Failed to deactivate blacklist mode: ${deactivateResponse.status}`);
            }
            
            const deactivateResult = await deactivateResponse.json();
            if (!deactivateResult.success) {
              throw new Error(deactivateResult.message || "Failed to deactivate blacklist mode");
            }
            
            setBlacklistModeActive(false);
            console.log("Blacklist mode deactivated successfully");
          }
          
          // Set speed limit before activating
          if (whitelistSpeedLimit) {
            console.log("Setting whitelist speed limit...");
            const limitResponse = await fetch("http://localhost:5000/whitelist/limit-rate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ rate: whitelistSpeedLimit })
            });
            
            if (!limitResponse.ok) {
              throw new Error(`Failed to set speed limit: ${limitResponse.status}`);
            }
            
            const limitResult = await limitResponse.json();
            if (!limitResult.success) {
              throw new Error(limitResult.message || "Failed to set speed limit");
            }
            console.log("Whitelist speed limit set successfully");
          }
          
          // Activate whitelist mode
          console.log("Activating whitelist mode...");
          const response = await fetch("http://localhost:5000/whitelist/activate", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              setWhitelistModeActive(true);
              console.log("Whitelist mode activated successfully");
            } else {
              throw new Error(result.message || "Failed to activate whitelist mode");
            }
          } else {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
        } else {
          // Deactivate whitelist mode
          console.log("Deactivating whitelist mode...");
          const response = await fetch("http://localhost:5000/whitelist/deactivate", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              setWhitelistModeActive(false);
              console.log("Whitelist mode deactivated successfully");
            } else {
              throw new Error(result.message || "Failed to deactivate whitelist mode");
            }
          } else {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
        }
      } catch (error) {
        console.error("Error toggling whitelist mode:", error);
        alert(`Failed to ${whitelistModeActive ? 'deactivate' : 'activate'} whitelist mode: ${error.message}`);
      } finally {
        setLoadingWhitelistMode(false);
      }
    } else {
      // Handle blacklist mode
      setLoadingBlacklistMode(true);
      try {
        if (!blacklistModeActive) {
          // If whitelist is active, deactivate it first
          if (whitelistModeActive) {
            console.log("Deactivating whitelist mode before activating blacklist...");
            const deactivateResponse = await fetch("http://localhost:5000/whitelist/deactivate", {
              method: "POST",
              headers: { "Content-Type": "application/json" }
            });
            
            if (!deactivateResponse.ok) {
              throw new Error(`Failed to deactivate whitelist mode: ${deactivateResponse.status}`);
            }
            
            const deactivateResult = await deactivateResponse.json();
            if (!deactivateResult.success) {
              throw new Error(deactivateResult.message || "Failed to deactivate whitelist mode");
            }
            
            setWhitelistModeActive(false);
            console.log("Whitelist mode deactivated successfully");
          }
          
          // Set speed limit before activating
          if (blacklistSpeedLimit) {
            console.log("Setting blacklist speed limit...");
            const limitResponse = await fetch("http://localhost:5000/blacklist/limit-rate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ rate: blacklistSpeedLimit })
            });
            
            if (!limitResponse.ok) {
              throw new Error(`Failed to set speed limit: ${limitResponse.status}`);
            }
            
            const limitResult = await limitResponse.json();
            if (!limitResult.success) {
              throw new Error(limitResult.message || "Failed to set speed limit");
            }
            console.log("Blacklist speed limit set successfully");
          }
          
          // Activate blacklist mode
          console.log("Activating blacklist mode...");
          const response = await fetch("http://localhost:5000/blacklist/activate", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              setBlacklistModeActive(true);
              console.log("Blacklist mode activated successfully");
            } else {
              throw new Error(result.message || "Failed to activate blacklist mode");
            }
          } else {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
        } else {
          // Deactivate blacklist mode
          console.log("Deactivating blacklist mode...");
          const response = await fetch("http://localhost:5000/blacklist/deactivate", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.success) {
              setBlacklistModeActive(false);
              console.log("Blacklist mode deactivated successfully");
            } else {
              throw new Error(result.message || "Failed to deactivate blacklist mode");
            }
          } else {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
        }
      } catch (error) {
        console.error("Error toggling blacklist mode:", error);
        alert(`Failed to ${blacklistModeActive ? 'deactivate' : 'activate'} blacklist mode: ${error.message}`);
      } finally {
        setLoadingBlacklistMode(false);
      }
    }
  };

  // Listen for changes in localStorage to update scanned devices count
  useEffect(() => {
    const handleStorageChange = () => {
      const savedDevices = localStorage.getItem("scannedDevices");
      if (savedDevices) {
        setScannedDevices(JSON.parse(savedDevices));
      }
    };

    const handleWhitelistUpdate = () => {
      fetchWhitelistData();
    };

    const handleBlacklistUpdate = () => {
      fetchBlacklistData();
    };

    // Listen for storage events (when localStorage changes from other tabs/components)
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('storage', handleWhitelistUpdate);
    window.addEventListener('storage', handleBlacklistUpdate);
    
    // Also check for updates periodically in case localStorage was updated in the same tab
    const interval = setInterval(handleStorageChange, 1000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('storage', handleWhitelistUpdate);
      window.removeEventListener('storage', handleBlacklistUpdate);
      clearInterval(interval);
    };
  }, []);

  // Initial data fetch
  useEffect(() => {
    const initializeData = async () => {
      try {
        await Promise.all([
          fetchWhitelistData(),
          fetchBlacklistData(),
          fetchWhitelistMode(),
          fetchBlacklistMode(),
          fetchWhitelistSpeedLimit(),
          fetchBlacklistSpeedLimit()
        ]);
      } catch (error) {
        console.error("Error initializing data:", error);
      }
    };

    initializeData();
  }, []);

  // Update localStorage when mode changes
  useEffect(() => {
    localStorage.setItem("controlPageMode", isWhitelistMode ? "whitelist" : "blacklist");
  }, [isWhitelistMode]);

  const handleSpeedTest = async () => {
    setIsSpeedTesting(true);
    try {
      const response = await fetch("http://localhost:5000/api/speedtest");
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      
      if (data.success && data.data) {
        setDownload(data.data.download);
        setUpload(data.data.upload);
        // Save to localStorage
        localStorage.setItem("speedTestResults", JSON.stringify({
          download: data.data.download,
          upload: data.data.upload,
          timestamp: new Date().toISOString()
        }));
      } else {
        throw new Error(data.message || "Speed test failed");
      }
    } catch (error) {
      console.error("Speed test error:", error);
      setDownload("Error");
      setUpload("Error");
      // Save error state to localStorage
      localStorage.setItem("speedTestResults", JSON.stringify({
        download: "Error",
        upload: "Error",
        timestamp: new Date().toISOString()
      }));
    } finally {
      setIsSpeedTesting(false);
    }
  };

  const handleDeleteDevice = async (deviceToRemove) => {
    if (isWhitelistMode) {
      try {
        const result = await whitelistAPI.remove(deviceToRemove.id);
        if (result.success) {
          // Remove from local state
          setDevices(devices.filter((d) => d.id !== deviceToRemove.id));
        } else {
          alert(`Failed to remove device: ${result.error?.message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error("Error removing device from whitelist:", error);
        alert("Failed to remove device from whitelist");
      }
    } else {
      try {
        const result = await blacklistAPI.remove(deviceToRemove.id);
        if (result.success) {
          // Remove from local state
          setBlacklistedDevices(blacklistedDevices.filter((d) => d.id !== deviceToRemove.id));
        } else {
          alert(`Failed to remove device: ${result.error?.message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error("Error removing device from blacklist:", error);
        alert("Failed to remove device from blacklist");
      }
    }
  };

  const toggleMode = () => {
    setIsWhitelistMode(!isWhitelistMode);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-8 px-4 sm:px-6 flex flex-col items-center w-full overflow-x-hidden">
      <div className="w-full max-w-4xl flex flex-col md:flex-row gap-6 md:gap-8 mb-8 md:mb-10">
        {/* Network Status */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow p-6 sm:p-8 flex flex-col gap-6 min-w-0">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold dark:text-white">Network Status</h2>
            <button
              onClick={handleSpeedTest}
              disabled={isSpeedTesting}
              className={`px-4 py-2 text-sm rounded-lg font-medium transition ${
                isSpeedTesting 
                  ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed" 
                  : "bg-blue-500 hover:bg-blue-600 text-white"
              }`}
            >
              {isSpeedTesting ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Testing...
                </div>
              ) : (
                "Speed Test"
              )}
            </button>
          </div>
          <div className="flex flex-wrap gap-4 sm:gap-6 mb-4">
            <StatusBox 
              label="Download" 
              value={download} 
              unit={download !== "-" && download !== "Error" ? "Mbps" : null}
              subtitle={download !== "-" ? `Last: ${getSpeedTestTimestamp() || "Unknown"}` : "Run speed test"}
            />
            <StatusBox 
              label="Upload" 
              value={upload} 
              unit={upload !== "-" && upload !== "Error" ? "Mbps" : null}
              subtitle={upload !== "-" ? `Last: ${getSpeedTestTimestamp() || "Unknown"}` : "Run speed test"}
            />
            <StatusBox label="Whitelisted" value={whitelisted} />
            <StatusBox label="Blacklisted" value={blacklisted} />
            <StatusBox 
              label="Active Devices" 
              value={activeDevices} 
              subtitle={activeDevices === 0 ? "Run a scan to see devices" : null}
            />
          </div>
          {(whitelistModeActive || blacklistModeActive) && (
            <div className={`${whitelistModeActive ? 'bg-green-50 dark:bg-green-900/40 text-green-600 dark:text-green-300 border-green-200 dark:border-green-400/30' : 'bg-red-50 dark:bg-red-900/40 text-red-600 dark:text-red-300 border-red-200 dark:border-red-400/30'} rounded-lg p-4 text-sm font-medium border`}>
              <span>• {whitelistModeActive ? 'Whitelist' : 'Blacklist'} mode is currently active</span>
            </div>
          )}
        </div>
        {/* Access Control Mode */}
        <div className="w-full md:w-1/3 bg-white dark:bg-gray-800 rounded-xl shadow p-6 sm:p-8 flex flex-col gap-6 min-w-0 mt-6 md:mt-0">
          <h2 className="text-xl font-semibold mb-4 dark:text-white">Access Control Mode</h2>
          <div className="mb-6">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
              Current Status: <span className={`font-semibold ${(whitelistModeActive || blacklistModeActive) ? 'text-green-600' : 'text-red-600'}`}>
                {(whitelistModeActive || blacklistModeActive) ? 'Active' : 'Inactive'}
              </span>
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {whitelistModeActive 
                ? "Only whitelisted devices have full network access" 
                : blacklistModeActive
                ? "Blacklisted devices have limited network access"
                : "All devices have normal network access"
              }
            </p>
          </div>
          
          {/* Speed Limit Input based on current mode */}
          <div className="mb-6">
            <label className="text-sm mb-2 block dark:text-gray-300">
              {isWhitelistMode ? 'Whitelist' : 'Blacklist'} Speed Limit (Mbps)
            </label>
            <input
              type="number"
              min={1}
              className="border rounded-lg px-4 py-3 mb-4 bg-white dark:bg-gray-900 dark:text-white dark:border-gray-700 w-full"
              value={isWhitelistMode ? whitelistSpeedLimit : blacklistSpeedLimit}
              onChange={e => isWhitelistMode ? setWhitelistSpeedLimit(e.target.value) : setBlacklistSpeedLimit(e.target.value)}
              placeholder="Enter speed limit"
              disabled={(isWhitelistMode ? whitelistModeActive : blacklistModeActive) || (loadingWhitelistMode || loadingBlacklistMode)}
            />
            
            {/* Single Activate/Deactivate Button */}
            <button
              className={`${
                (isWhitelistMode ? whitelistModeActive : blacklistModeActive)
                  ? "bg-red-500 hover:bg-red-600" 
                  : isWhitelistMode 
                    ? "bg-green-500 hover:bg-green-600"
                    : "bg-orange-500 hover:bg-orange-600"
              } text-white font-semibold rounded-lg py-3 transition w-full flex items-center justify-center gap-3`}
              onClick={handleToggleAccessControl}
              disabled={loadingWhitelistMode || loadingBlacklistMode}
            >
              {(loadingWhitelistMode || loadingBlacklistMode) ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </>
              ) : (
                (isWhitelistMode ? whitelistModeActive : blacklistModeActive) 
                  ? `Deactivate ${isWhitelistMode ? 'Whitelist' : 'Blacklist'} Mode`
                  : `Activate ${isWhitelistMode ? 'Whitelist' : 'Blacklist'} Mode`
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mode Toggle Button */}
      <div className="w-full max-w-4xl mb-6">
        <button
          onClick={toggleMode}
          className="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-xl shadow px-6 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
        >
          {isWhitelistMode ? (
            <>
              <Shield className="w-5 h-5 text-green-500" />
              <span className="text-gray-700 dark:text-gray-300">Switch to Blacklist Mode</span>
            </>
          ) : (
            <>
              <ShieldOff className="w-5 h-5 text-red-500" />
              <span className="text-gray-700 dark:text-gray-300">Switch to Whitelist Mode</span>
            </>
          )}
        </button>
      </div>

      {/* Device List */}
      <div className="w-full max-w-4xl bg-white dark:bg-gray-800 rounded-xl shadow p-6 sm:p-8">
        <h2 className="text-xl font-semibold mb-6 dark:text-white">
          {isWhitelistMode ? "Whitelisted Devices" : "Blacklisted Devices"}
        </h2>
        <div className="flex flex-col gap-4 max-h-96 overflow-y-auto">
          {(isWhitelistMode ? devices : blacklistedDevices).map((device) => (
            <div
              key={device.id || device.mac_address}
              className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-gray-50 dark:bg-gray-900 rounded-lg p-4 gap-3 sm:gap-0"
            >
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {device.device_name || device.hostname || device.name || "Unknown Device"}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  MAC: {device.mac_address || device.mac}
                </div>
                {(device.reason || device.description) && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {device.reason || device.description}
                  </div>
                )}
              </div>
              <button
                className="p-3 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/40 self-end sm:self-auto"
                onClick={() => handleDeleteDevice(device)}
                title={`Remove from ${isWhitelistMode ? 'whitelist' : 'blacklist'}`}
              >
                <Trash2 className="w-5 h-5 text-red-500" />
              </button>
            </div>
          ))}
          {isWhitelistMode && devices.length === 0 && (
            <div className="text-center py-6 text-gray-500 dark:text-gray-400">
              No devices in whitelist. Go to Scan page to add devices.
            </div>
          )}
          {!isWhitelistMode && blacklistedDevices.length === 0 && (
            <div className="text-center py-6 text-gray-500 dark:text-gray-400">
              No devices in blacklist. Add devices to blacklist to restrict their access.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBox({ label, value, unit, subtitle }) {
  return (
    <div className="flex flex-col items-center bg-gray-50 dark:bg-gray-900 rounded-lg px-3 py-3 min-w-[100px] max-w-[140px] flex-1">
      <span className="text-sm text-gray-500 dark:text-gray-300 mb-1 text-center">{label}</span>
      <div className="flex flex-col items-center">
        <span className="text-xl font-bold text-gray-800 dark:text-white text-center break-all">
          {value}
        </span>
        {unit && (
          <span className="text-sm font-normal text-gray-600 dark:text-gray-400">
            {unit}
          </span>
        )}
      </div>
      {subtitle && (
        <span className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
          {subtitle}
        </span>
      )}
    </div>
  );
}
