import React, { useState, useEffect } from "react";
import { Trash2, Shield, ShieldOff } from "lucide-react";

const mockDevices = [
  { name: "iPhone 13", mac: "00:1A:2B:3C:4D:5E" },
  { name: "iPad Pro", mac: "00:3C:4D:5E:6F:7G" },
];

const mockBlacklistedDevices = [
  { name: "Unknown Device", mac: "00:2B:3C:4D:5E:6F" },
  { name: "Suspicious Device", mac: "00:4D:5E:6F:7G:8H" },
];

export default function ControlPage() {

  const [devices, setDevices] = useState([]);
  const [blacklistedDevices, setBlacklistedDevices] = useState(mockBlacklistedDevices);
  const [isWhitelistMode, setIsWhitelistMode] = useState(true);
  const [whitelistModeActive, setWhitelistModeActive] = useState(false);
  const [loadingWhitelistMode, setLoadingWhitelistMode] = useState(false);
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
      const response = await fetch("http://localhost:5000/whitelist");
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setDevices(result.data || []);
        }
      }
    } catch (error) {
      console.error("Error fetching whitelist:", error);
    }
  };

  // Fetch whitelist mode status
  const fetchWhitelistMode = async () => {
    try {
      const response = await fetch("http://localhost:5000/whitelist/mode");
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setWhitelistModeActive(result.data);
        }
      }
    } catch (error) {
      console.error("Error fetching whitelist mode:", error);
    }
  };

  // Fetch whitelist speed limit
  const fetchWhitelistSpeedLimit = async () => {
    try {
      const response = await fetch("http://localhost:5000/whitelist/limit_rate", { method: "GET" });
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setWhitelistSpeedLimit(result.data.rate || "");
        }
      }
    } catch (error) {
      console.error("Error fetching whitelist speed limit:", error);
    }
  };

  // Toggle whitelist mode
  const handleToggleWhitelistMode = async () => {
    setLoadingWhitelistMode(true);
    try {
      if (!whitelistModeActive) {
        // Set speed limit before activating
        await fetch("http://localhost:5000/whitelist/limit_rate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rate: whitelistSpeedLimit })
        });
      }
      const method = whitelistModeActive ? "DELETE" : "POST";
      const response = await fetch("http://localhost:5000/whitelist/mode", {
        method: method,
        headers: { "Content-Type": "application/json" }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setWhitelistModeActive(!whitelistModeActive);
        } else {
          throw new Error(result.message);
        }
      } else {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
    } catch (error) {
      console.error("Error toggling whitelist mode:", error);
      alert(`Failed to ${whitelistModeActive ? 'deactivate' : 'activate'} whitelist mode: ${error.message}`);
    } finally {
      setLoadingWhitelistMode(false);
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

    // Listen for storage events (when localStorage changes from other tabs/components)
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('storage', handleWhitelistUpdate);
    
    // Also check for updates periodically in case localStorage was updated in the same tab
    const interval = setInterval(handleStorageChange, 1000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('storage', handleWhitelistUpdate);
      clearInterval(interval);
    };
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchWhitelistData();
    fetchWhitelistMode();
    fetchWhitelistSpeedLimit();
  }, []);

  const handleSpeedTest = async () => {
    setIsSpeedTesting(true);
    try {
      const response = await fetch("http://localhost:5000/api/speed_test");
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
        const response = await fetch("http://localhost:5000/whitelist", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ip: deviceToRemove.ip })
        });
        
        if (response.ok) {
          const result = await response.json();
          if (result.success) {
            // Remove from local state
            setDevices(devices.filter((d) => d.ip !== deviceToRemove.ip));
          } else {
            alert(`Failed to remove device: ${result.message}`);
          }
        } else {
          alert("Failed to remove device from whitelist");
        }
      } catch (error) {
        console.error("Error removing device from whitelist:", error);
        alert("Failed to remove device from whitelist");
      }
    } else {
      setBlacklistedDevices(blacklistedDevices.filter((d) => d.mac !== deviceToRemove.mac));
      // Call backend to remove from blacklist
    }
  };

  const toggleMode = () => {
    setIsWhitelistMode(!isWhitelistMode);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-6 px-2 sm:px-4 flex flex-col items-center w-full overflow-x-hidden">
      <div className="w-full max-w-3xl flex flex-col md:flex-row gap-4 md:gap-6 mb-6 md:mb-8">
        {/* Network Status */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6 flex flex-col gap-4 min-w-0">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-semibold dark:text-white">Network Status</h2>
            <button
              onClick={handleSpeedTest}
              disabled={isSpeedTesting}
              className={`px-3 py-1 text-sm rounded-lg font-medium transition ${
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
          <div className="flex flex-wrap gap-2 sm:gap-4 mb-2">
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
          {whitelistModeActive && (
            <div className="bg-green-50 dark:bg-green-900/40 text-green-600 dark:text-green-300 rounded p-2 text-sm font-medium border border-green-200 dark:border-green-400/30">
              <span>• Whitelist mode is currently active</span>
            </div>
          )}
        </div>
        {/* Whitelist Mode Control */}
        <div className="w-full md:w-1/3 bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6 flex flex-col gap-4 min-w-0 mt-4 md:mt-0">
          <h2 className="text-lg font-semibold mb-2 dark:text-white">Access Control Mode</h2>
          <div className="mb-3">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
              Current Status: <span className={`font-semibold ${whitelistModeActive ? 'text-green-600' : 'text-red-600'}`}>
                {whitelistModeActive ? 'Active' : 'Inactive'}
              </span>
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {whitelistModeActive 
                ? "Only whitelisted devices have full network access" 
                : "All devices have normal network access"
              }
            </p>
          </div>
          <label className="text-sm mb-1 dark:text-gray-300 mt-2">Speed Limit (Mbps)</label>
          <input
            type="number"
            min={1}
            className="border rounded px-3 py-2 mb-1 bg-white dark:bg-gray-900 dark:text-white dark:border-gray-700 w-full"
            value={whitelistSpeedLimit}
            onChange={e => setWhitelistSpeedLimit(e.target.value)}
            placeholder="Enter speed limit"
            disabled={whitelistModeActive || loadingWhitelistMode}
          />
          {whitelistSpeedLimit && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              Current limit: {whitelistSpeedLimit} Mbps
            </div>
          )}
          <button
            className={`${
              whitelistModeActive 
                ? "bg-red-500 hover:bg-red-600" 
                : "bg-green-500 hover:bg-green-600"
            } text-white font-semibold rounded py-2 transition w-full flex items-center justify-center gap-2`}
            onClick={handleToggleWhitelistMode}
            disabled={loadingWhitelistMode}
          >
            {loadingWhitelistMode ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </>
            ) : (
              whitelistModeActive ? "Deactivate Whitelist Mode" : "Activate Whitelist Mode"
            )}
          </button>
        </div>
      </div>

      {/* Mode Toggle Button */}
      <div className="w-full max-w-3xl mb-4">
        <button
          onClick={toggleMode}
          className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-xl shadow px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
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
      <div className="w-full max-w-3xl bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">
          {isWhitelistMode ? "Whitelisted Devices" : "Blacklisted Devices"}
        </h2>
        <div className="flex flex-col gap-3 max-h-80 overflow-y-auto">
          {(isWhitelistMode ? devices : blacklistedDevices).map((device) => (
            <div
              key={device.ip || device.mac}
              className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-gray-50 dark:bg-gray-900 rounded p-3 gap-2 sm:gap-0"
            >
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  {device.name || device.hostname || "Unknown Device"}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  IP: {device.ip}
                </div>
                {device.description && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {device.description}
                  </div>
                )}
              </div>
              <button
                className="p-2 rounded hover:bg-red-100 dark:hover:bg-red-900/40 self-end sm:self-auto"
                onClick={() => handleDeleteDevice(device)}
                title={`Remove from ${isWhitelistMode ? 'whitelist' : 'blacklist'}`}
              >
                <Trash2 className="w-5 h-5 text-red-500" />
              </button>
            </div>
          ))}
          {isWhitelistMode && devices.length === 0 && (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              No devices in whitelist. Go to Scan page to add devices.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBox({ label, value, unit, subtitle }) {
  return (
    <div className="flex flex-col items-center bg-gray-50 dark:bg-gray-900 rounded-lg px-3 py-2 min-w-[80px] flex-1">
      <span className="text-sm text-gray-500 dark:text-gray-300">{label}</span>
      <span className="text-xl font-bold text-gray-800 dark:text-white">
        {value}
        {unit && <span className="text-base font-normal ml-1">{unit}</span>}
      </span>
      {subtitle && (
        <span className="text-xs text-gray-400 dark:text-gray-500 text-center mt-1">
          {subtitle}
        </span>
      )}
    </div>
  );
}
