import React, { useState, useEffect } from "react";
import { Trash2, Shield, ShieldOff, Plus, Edit, X } from "lucide-react";
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
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [formData, setFormData] = useState({
    mac_address: '',
    device_name: '',
    description: '',
    reason: ''
  });
  const [formLoading, setFormLoading] = useState(false);

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
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage");
        return;
      }
      const result = await whitelistAPI.getAll(routerId);
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
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage");
        return;
      }
      const result = await blacklistAPI.getAll(routerId);
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
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage for whitelist mode");
        return;
      }
      const result = await whitelistAPI.getModeStatus(routerId);
      if (result.success) {
        setWhitelistModeActive(result.data?.active || false);
      } else {
        console.error("Failed to fetch whitelist mode:", result.error);
      }
    } catch (error) {
      console.error("Error fetching whitelist mode:", error);
    }
  };

  // Fetch blacklist mode status
  const fetchBlacklistMode = async () => {
    try {
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage for blacklist mode");
        return;
      }
      const result = await blacklistAPI.getModeStatus(routerId);
      if (result.success) {
        setBlacklistModeActive(result.data?.active || false);
      } else {
        console.error("Failed to fetch blacklist mode:", result.error);
      }
    } catch (error) {
      console.error("Error fetching blacklist mode:", error);
    }
  };

  // Fetch whitelist speed limit
  const fetchWhitelistSpeedLimit = async () => {
    try {
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage for whitelist speed limit");
        return;
      }
      const result = await whitelistAPI.getLimitRate(routerId);
      if (result.success && result.data !== null && result.data !== undefined) {
        // Backend returns rate directly in data field (not data.rate)
        setWhitelistSpeedLimit(result.data.toString() || "");
      } else {
        console.error("Failed to fetch whitelist speed limit:", result.error);
      }
    } catch (error) {
      console.error("Error fetching whitelist speed limit:", error);
    }
  };

  // Fetch blacklist speed limit
  const fetchBlacklistSpeedLimit = async () => {
    try {
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        console.error("No routerId found in localStorage for blacklist speed limit");
        return;
      }
      const result = await blacklistAPI.getLimitRate(routerId);
      if (result.success && result.data !== null && result.data !== undefined) {
        // Backend returns rate directly in data field (not data.rate)
        setBlacklistSpeedLimit(result.data.toString() || "");
      } else {
        console.error("Failed to fetch blacklist speed limit:", result.error);
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
          // Get routerId for all operations
          const routerId = localStorage.getItem('routerId');
          if (!routerId) {
            throw new Error("No routerId found in localStorage");
          }

          // If blacklist is active, deactivate it first
          if (blacklistModeActive) {
            console.log("Deactivating blacklist mode before activating whitelist...");
            const deactivateResult = await blacklistAPI.deactivateMode(routerId);
            if (!deactivateResult.success) {
              throw new Error(deactivateResult.message || "Failed to deactivate blacklist mode");
            }
            
            setBlacklistModeActive(false);
            console.log("Blacklist mode deactivated successfully");
            
            // Wait a moment for the router to process the deactivation
            console.log("Waiting for router to process blacklist deactivation...");
            await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
            
            // Verify blacklist mode is actually off
            const verifyResult = await blacklistAPI.getModeStatus(routerId);
            if (verifyResult.success && verifyResult.data?.active) {
              throw new Error("Blacklist mode is still active after deactivation attempt");
            }
            console.log("Blacklist mode deactivation confirmed");
          }
          
          // Always set speed limit before activating (use current value or default)
          const currentRate = whitelistSpeedLimit || "50"; // Default to 50 Mbps if empty
          const rateValue = parseInt(currentRate, 10);
          if (isNaN(rateValue) || rateValue < 1 || rateValue > 1000) {
            throw new Error("Speed limit must be a number between 1 and 1000 Mbps");
          }
          
          console.log(`Setting whitelist speed limit to ${rateValue} Mbps...`);
          const limitResult = await whitelistAPI.setLimitRate(routerId, rateValue);
          if (!limitResult.success) {
            throw new Error(limitResult.message || "Failed to set speed limit");
          }
          console.log("Whitelist speed limit set successfully");
          
          // Update the UI to reflect the rate that was actually set
          setWhitelistSpeedLimit(rateValue.toString());
          
          // Activate whitelist mode
          console.log("Activating whitelist mode...");
          const result = await whitelistAPI.activateMode(routerId);
          if (result.success) {
            setWhitelistModeActive(true);
            console.log("Whitelist mode activated successfully");
            
            // Final verification that the mode switch was successful
            console.log("Verifying whitelist mode activation...");
            const finalCheck = await whitelistAPI.getModeStatus(routerId);
            if (!finalCheck.success || !finalCheck.data?.active) {
              console.warn("Warning: Whitelist mode may not be fully active yet");
            } else {
              console.log("Whitelist mode activation confirmed");
            }
          } else {
            throw new Error(result.message || "Failed to activate whitelist mode");
          }
        } else {
          // Deactivate whitelist mode
          console.log("Deactivating whitelist mode...");
          const routerId = localStorage.getItem('routerId');
          if (!routerId) {
            throw new Error("No routerId found in localStorage");
          }
          const result = await whitelistAPI.deactivateMode(routerId);
          if (result.success) {
            setWhitelistModeActive(false);
            console.log("Whitelist mode deactivated successfully");
          } else {
            throw new Error(result.message || "Failed to deactivate whitelist mode");
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
            const routerId = localStorage.getItem('routerId');
            if (!routerId) {
              throw new Error("No routerId found in localStorage");
            }
            const deactivateResult = await whitelistAPI.deactivateMode(routerId);
            if (!deactivateResult.success) {
              throw new Error(deactivateResult.message || "Failed to deactivate whitelist mode");
            }
            
            setWhitelistModeActive(false);
            console.log("Whitelist mode deactivated successfully");
            
            // Wait a moment for the router to process the deactivation
            console.log("Waiting for router to process whitelist deactivation...");
            await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
            
            // Verify whitelist mode is actually off
            const verifyResult = await whitelistAPI.getModeStatus(routerId);
            if (verifyResult.success && verifyResult.data?.active) {
              throw new Error("Whitelist mode is still active after deactivation attempt");
            }
            console.log("Whitelist mode deactivation confirmed");
          }
          
          // Set speed limit before activating
          const routerId = localStorage.getItem('routerId');
          if (!routerId) {
            throw new Error("No routerId found in localStorage");
          }
          
          const currentRate = blacklistSpeedLimit || "50"; // Default to 50 Mbps if empty
          const rateValue = parseInt(currentRate, 10);
          if (isNaN(rateValue) || rateValue < 1 || rateValue > 1000) {
            throw new Error("Speed limit must be a number between 1 and 1000 Mbps");
          }
          
          console.log(`Setting blacklist speed limit to ${rateValue} Mbps...`);
          const limitResult = await blacklistAPI.setLimitRate(routerId, rateValue);
          if (!limitResult.success) {
            throw new Error(limitResult.message || "Failed to set speed limit");
          }
          console.log("Blacklist speed limit set successfully");
          
          // Update the UI to reflect the rate that was actually set
          setBlacklistSpeedLimit(rateValue.toString());
          
          // Activate blacklist mode
          console.log("Activating blacklist mode...");
          const result = await blacklistAPI.activateMode(routerId);
          if (result.success) {
            setBlacklistModeActive(true);
            console.log("Blacklist mode activated successfully");
            
            // Final verification that the mode switch was successful
            console.log("Verifying blacklist mode activation...");
            const finalCheck = await blacklistAPI.getModeStatus(routerId);
            if (!finalCheck.success || !finalCheck.data?.active) {
              console.warn("Warning: Blacklist mode may not be fully active yet");
            } else {
              console.log("Blacklist mode activation confirmed");
            }
          } else {
            throw new Error(result.message || "Failed to activate blacklist mode");
          }
        } else {
          // Deactivate blacklist mode
          console.log("Deactivating blacklist mode...");
          const routerId = localStorage.getItem('routerId');
          if (!routerId) {
            throw new Error("No routerId found in localStorage");
          }
          const result = await blacklistAPI.deactivateMode(routerId);
          if (result.success) {
            setBlacklistModeActive(false);
            console.log("Blacklist mode deactivated successfully");
          } else {
            throw new Error(result.message || "Failed to deactivate blacklist mode");
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
      // Use Promise.allSettled to prevent one failure from stopping all others
      const results = await Promise.allSettled([
        fetchWhitelistData(),
        fetchBlacklistData(),
        fetchWhitelistMode(),
        fetchBlacklistMode(),
        fetchWhitelistSpeedLimit(),
        fetchBlacklistSpeedLimit()
      ]);
      
      // Log any failures for debugging
      results.forEach((result, index) => {
        const functionNames = [
          'fetchWhitelistData',
          'fetchBlacklistData', 
          'fetchWhitelistMode',
          'fetchBlacklistMode',
          'fetchWhitelistSpeedLimit',
          'fetchBlacklistSpeedLimit'
        ];
        
        if (result.status === 'rejected') {
          console.warn(`${functionNames[index]} failed:`, result.reason);
        }
      });
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

  const handleAddDevice = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      const routerId = localStorage.getItem('routerId');
      if (!routerId) {
        throw new Error("No routerId found in localStorage");
      }

      let result;
      if (isWhitelistMode) {
        result = await whitelistAPI.add(routerId, {
          mac_address: formData.mac_address,
          device_name: formData.device_name,
          description: formData.description
        });
      } else {
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          alert('No routerId found in localStorage');
          return;
        }
        result = await blacklistAPI.add(routerId, {
          mac_address: formData.mac_address,
          device_name: formData.device_name,
          reason: formData.reason
        });
      }

      if (result.success) {
        // Refresh the appropriate list
        if (isWhitelistMode) {
          const updatedDevices = await whitelistAPI.getAll(routerId);
          if (updatedDevices.success) {
            setDevices(updatedDevices.data?.devices || []);
          }
        } else {
          const routerId = localStorage.getItem('routerId');
          if (routerId) {
            const updatedDevices = await blacklistAPI.getAll(routerId);
            if (updatedDevices.success) {
              setBlacklistedDevices(updatedDevices.data?.devices || []);
            }
          }
        }
        
        // Reset form
        setFormData({ mac_address: '', device_name: '', description: '', reason: '' });
        setShowAddForm(false);
      } else {
        alert(`Failed to add device: ${result.error?.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Error adding device:", error);
      alert("Failed to add device");
    } finally {
      setFormLoading(false);
    }
  };

  const handleEditDevice = (device) => {
    setEditingDevice(device);
    setFormData({
      mac_address: device.mac_address || '',
      device_name: device.device_name || '',
      description: device.description || '',
      reason: device.reason || ''
    });
    setShowAddForm(true);
  };

  const handleUpdateDevice = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      let result;
      if (isWhitelistMode) {
        result = await whitelistAPI.update(editingDevice.id, {
          device_name: formData.device_name,
          description: formData.description
        });
      } else {
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          alert('No routerId found in localStorage');
          return;
        }
        result = await blacklistAPI.update(routerId, editingDevice.id, {
          device_name: formData.device_name,
          reason: formData.reason
        });
      }

      if (result.success) {
        // Refresh the appropriate list
        if (isWhitelistMode) {
          const updatedDevices = await whitelistAPI.getAll(routerId);
          if (updatedDevices.success) {
            setDevices(updatedDevices.data?.devices || []);
          }
        } else {
          const routerId = localStorage.getItem('routerId');
          if (routerId) {
            const updatedDevices = await blacklistAPI.getAll(routerId);
            if (updatedDevices.success) {
              setBlacklistedDevices(updatedDevices.data?.devices || []);
            }
          }
        }
        
        // Reset form
        setFormData({ mac_address: '', device_name: '', description: '', reason: '' });
        setShowAddForm(false);
        setEditingDevice(null);
      } else {
        alert(`Failed to update device: ${result.error?.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Error updating device:", error);
      alert("Failed to update device");
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteDevice = async (deviceToRemove) => {
    if (!window.confirm(`Are you sure you want to remove this device from the ${isWhitelistMode ? 'whitelist' : 'blacklist'}?`)) {
      return;
    }

    if (isWhitelistMode) {
      try {
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          alert('No routerId found in localStorage');
          return;
        }
        const result = await whitelistAPI.remove(routerId, { ip: deviceToRemove.ip });
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
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          alert('No routerId found in localStorage');
          return;
        }
        const result = await blacklistAPI.remove(routerId, { ip: deviceToRemove.ip });
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

  const handleCancelForm = () => {
    setFormData({ mac_address: '', device_name: '', description: '', reason: '' });
    setShowAddForm(false);
    setEditingDevice(null);
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
              max={1000}
              className="border rounded-lg px-4 py-3 mb-4 bg-white dark:bg-gray-900 dark:text-white dark:border-gray-700 w-full"
              value={isWhitelistMode ? whitelistSpeedLimit : blacklistSpeedLimit}
              onChange={e => isWhitelistMode ? setWhitelistSpeedLimit(e.target.value) : setBlacklistSpeedLimit(e.target.value)}
              placeholder="Enter speed limit (1-1000 Mbps)"
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
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold dark:text-white">
            {isWhitelistMode ? "Whitelisted Devices" : "Blacklisted Devices"}
          </h2>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition"
          >
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        </div>

        {/* Add/Edit Form */}
        {showAddForm && (
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium dark:text-white">
                {editingDevice ? 'Edit Device' : `Add Device to ${isWhitelistMode ? 'Whitelist' : 'Blacklist'}`}
              </h3>
              <button
                onClick={handleCancelForm}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <form onSubmit={editingDevice ? handleUpdateDevice : handleAddDevice} className="space-y-4">
              {!editingDevice && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    MAC Address *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.mac_address}
                    onChange={(e) => setFormData({ ...formData, mac_address: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 dark:text-white"
                    placeholder="AA:BB:CC:DD:EE:FF"
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Device Name
                </label>
                <input
                  type="text"
                  value={formData.device_name}
                  onChange={(e) => setFormData({ ...formData, device_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 dark:text-white"
                  placeholder="Enter device name"
                />
              </div>
              
              {isWhitelistMode ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 dark:text-white"
                    placeholder="Enter device description"
                    rows="3"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Reason
                  </label>
                  <textarea
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 dark:text-white"
                    placeholder="Enter reason for blacklisting"
                    rows="3"
                  />
                </div>
              )}
              
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg transition"
                >
                  {formLoading ? 'Saving...' : (editingDevice ? 'Update Device' : `Add to ${isWhitelistMode ? 'Whitelist' : 'Blacklist'}`)}
                </button>
                <button
                  type="button"
                  onClick={handleCancelForm}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Devices List */}
        <div className="flex flex-col gap-4 max-h-96 overflow-y-auto">
          {(isWhitelistMode ? devices : blacklistedDevices).map((device) => (
            <div
              key={device.id || device.mac_address}
              className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-gray-50 dark:bg-gray-900 rounded-lg p-4 gap-3 sm:gap-0"
            >
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">
                  {device.device_name || device.hostname || device.name || "Unknown Device"}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  IP: {device.ip} • MAC: {device.mac_address || device.mac}
                </div>
                {device.created_at && (
                  <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Added: {new Date(device.created_at).toLocaleDateString()}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEditDevice(device)}
                  className="p-2 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
                  title="Edit device"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteDevice(device)}
                  className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                  title={`Remove from ${isWhitelistMode ? 'whitelist' : 'blacklist'}`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {isWhitelistMode && devices.length === 0 && !showAddForm && (
            <div className="text-center py-6 text-gray-500 dark:text-gray-400">
              No devices in whitelist. Add devices to grant them full network access.
            </div>
          )}
          {!isWhitelistMode && blacklistedDevices.length === 0 && !showAddForm && (
            <div className="text-center py-6 text-gray-500 dark:text-gray-400">
              No devices in blacklist. Add devices to restrict their network access.
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
