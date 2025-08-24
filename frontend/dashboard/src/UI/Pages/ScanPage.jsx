import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { FaBan } from "react-icons/fa";
import DeviceCard from "../DeviceCard";
import ScannerAnimation from "../../components/ScannerAnimation";
import ScanButton from "../../components/ScanButton";
import { networkAPI, devicesAPI, blockedDevicesAPI } from "../../constants/api";
// import { staticDevices } from "../../constants/index";
const iconMap = {
  router: "BsRouter",
  laptop: "FaLaptop",
  mobile: "FaMobileAlt",
  tv: "FaTv",
};

const identifyDeviceType = (hostname, ip) => {
  if (hostname.toLowerCase().includes("router") || ip.endsWith(".1"))
    return "router";
  if (
    hostname.toLowerCase().includes("laptop") ||
    hostname.toLowerCase().includes("desktop")
  )
    return "laptop";
  if (
    hostname.toLowerCase().includes("phone") ||
    hostname.toLowerCase().includes("mobile")
  )
    return "mobile";
  if (hostname.toLowerCase().includes("tv")) return "tv";
  return "unknown";

};

const formatDevices = (data) => {
  return data.map(({ hostname, ip, mac }) => {
    const type = identifyDeviceType(hostname, ip);
    return {
      type,
      hostname: hostname !== "Unknown" ? hostname : "Unnamed Device",
      ip,
      mac,
      icon: iconMap[type] || "FaRegQuestionCircle",
    };
  });
};

const getFormattedDate = () => {
  const now = new Date();
  const day = now.getDate().toString().padStart(2, "0");
  const month = (now.getMonth() + 1).toString().padStart(2, "0");
  const year = now.getFullYear();
  const hours = now.getHours().toString().padStart(2, "0");
  const minutes = now.getMinutes().toString().padStart(2, "0");

  return `${day}/${month}/${year}, ${hours}:${minutes}`;
};

const ScanPage = () => {
  const [devices, setDevices] = useState(() => {
    const savedDevices = localStorage.getItem("scannedDevices");
    return savedDevices ? JSON.parse(savedDevices) : [];
  });
  const [blockedDevices, setBlockedDevices] = useState([]);
  const [error, setError] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(() => {
    return localStorage.getItem("lastScanTime") || null;
  });
  
  // Local blocked devices state for immediate UI updates
  const [localBlockedDevices, setLocalBlockedDevices] = useState([]);

  const isMounted = useRef(true);
  const location = useLocation();

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    localStorage.setItem("scannedDevices", JSON.stringify(devices));
  }, [devices]);

  // Load blocked devices on component mount
  useEffect(() => {
    loadBlockedDevices();
  }, []);

  // Load blocked devices from backend
  const loadBlockedDevices = async () => {
    const routerId = localStorage.getItem("routerId");
    if (!routerId) return;
    
    try {
      const response = await blockedDevicesAPI.getBlockedDevices(routerId);
      if (response.success) {
        const blockedData = response.data || [];
        setBlockedDevices(blockedData);
        // Sync local state with backend state
        setLocalBlockedDevices(blockedData);
      }
    } catch (error) {
      console.error('Error loading blocked devices:', error);
    }
  };

  // Handle immediate blocked device updates (for eager UI)
  const handleImmediateBlockUpdate = (device, isBlocked) => {
    if (isBlocked) {
      // Add to local blocked devices immediately
      const newBlockedDevice = {
        id: `temp_${Date.now()}`, // Temporary ID
        device_ip: device.ip,
        device_mac: device.mac,
        device_info: {
          hostname: device.hostname,
          device_name: device.hostname
        },
        blocked_at: new Date().toISOString(),
        is_temp: true // Flag to identify temporary entries
      };
      setLocalBlockedDevices(prev => [...prev, newBlockedDevice]);
    } else {
      // Remove from local blocked devices immediately
      setLocalBlockedDevices(prev => 
        prev.filter(b => !(b.device_ip === device.ip || 
          (b.device_mac && device.mac && b.device_mac.toLowerCase() === device.mac.toLowerCase())))
      );
    }
  };

  const handleUnblockDevice = async (blockedDeviceId) => {
    try {
      const routerId = localStorage.getItem("routerId");
      if (routerId) {
        const response = await blockedDevicesAPI.unblockDevice(routerId, blockedDeviceId);
        if (response.success) {
          // Refresh blocked devices list
          await loadBlockedDevices();
        }
      }
    } catch (error) {
      console.error("Failed to unblock device:", error);
    }
  };

  const handleNetworkScan = async () => {
    setIsScanning(true);
    setError(null);

    try {
      // Get routerId from localStorage or context  
      // Note: sessionId no longer needed - automatically derived from authenticated user
      const routerId = localStorage.getItem("routerId") || "<your_router_id>";
      
      // Use the new networkAPI helper function (handles authentication automatically)
      const data = await networkAPI.scan(routerId);

      if (isMounted.current) {
        const formattedDevices = formatDevices(data["data"]);

        // Save devices to localStorage first (for backward compatibility)
        setDevices(formattedDevices);
        const scanTime = getFormattedDate();
        setLastScanTime(scanTime);
        localStorage.setItem("lastScanTime", scanTime);

        // Also save devices to backend to get proper UUIDs
        try {
          console.log("Saving scanned devices to backend...");
          console.log("Router ID:", routerId);
          console.log("Devices to save:", formattedDevices);
          
          const bulkCreateResponse = await devicesAPI.bulkCreate(routerId, formattedDevices);
          const savedDevices = bulkCreateResponse.data || [];
          console.log("Successfully saved devices to backend:", savedDevices);
          
          // Update localStorage with the backend devices that have UUIDs
          if (savedDevices && savedDevices.length > 0) {
            localStorage.setItem("scannedDevices", JSON.stringify(savedDevices));
            setDevices(savedDevices);
            console.log("Updated localStorage with backend devices");
          }
        } catch (backendError) {
          console.error("Failed to save devices to backend:", backendError);
          console.error("Error details:", backendError.message);
          // Don't fail the whole scan if backend save fails
        }
      }
    } catch (err) {
      if (isMounted.current) {
        setError(`Error: ${err.message}`);
      }
    } finally {
      if (isMounted.current) {
        setIsScanning(false);
      }
    }
  };

  return (
    <div className="h-screen overflow-hidden">
      <div className="p-10 flex flex-col items-center h-full overflow-y-auto">
        <ScanButton onScan={handleNetworkScan} isScanning={isScanning} />

        {isScanning && (
          <div className="pt-20">
            <ScannerAnimation />
          </div>
        )}

        {error && <p className="text-red-600 mt-4">{error}</p>}

        {!isScanning && lastScanTime && (
          <p className="text-gray-500 my-4 text-lg font-medium">
            Last scan: {lastScanTime}
          </p>
        )}

        {!isScanning && (
          <>
            {/* Scanned Devices Section */}
            <div className="pt-7 w-full flex justify-center">
              <div className="px-5 flex flex-wrap justify-center gap-6">
                {devices.map((device, index) => {
                  // Check if this device is blocked (use local state for immediate feedback)
                  const isBlocked = localBlockedDevices.some(blocked => 
                    blocked.device_ip === device.ip || 
                    (blocked.device_mac && device.mac && blocked.device_mac.toLowerCase() === device.mac.toLowerCase())
                  );
                  
                  return (
                    <DeviceCard 
                      key={index} 
                      device={device} 
                      onDeviceBlocked={loadBlockedDevices}
                      onImmediateBlockUpdate={handleImmediateBlockUpdate}
                      isBlocked={isBlocked}
                    />
                  );
                })}
              </div>
            </div>

            {/* Blocked Devices Section */}
            {localBlockedDevices.length > 0 && (
              <div className="pt-10 w-full">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Blocked Devices
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-2">
                    Devices that are currently blocked from network access
                  </p>
                </div>
                <div className="px-5 flex flex-wrap justify-center gap-6">
                  {localBlockedDevices.map((blockedDevice) => (
                    <div
                      key={blockedDevice.id}
                      className="bg-white dark:bg-gray-700 shadow-lg rounded-2xl p-5 flex flex-col items-center gap-3 w-72"
                    >
                      <div className="text-5xl text-red-500">
                        <FaBan />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white text-center">
                        {blockedDevice.device_info?.hostname || blockedDevice.device_info?.device_name || "Blocked Device"}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        IP: {blockedDevice.device_ip}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-300">
                        MAC: {blockedDevice.device_mac}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Blocked: {new Date(blockedDevice.blocked_at).toLocaleDateString()}
                      </p>
                      {blockedDevice.is_temp && (
                        <p className="text-xs text-blue-500 dark:text-blue-400">
                          Processing...
                        </p>
                      )}
                      <button
                        onClick={() => handleUnblockDevice(blockedDevice.id)}
                        className="p-2 rounded-full shadow-md transition bg-green-500 text-white hover:bg-green-600"
                        title="Unblock Device"
                      >
                        <span className="text-xs">Unblock</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ScanPage;
