import React, { useState, useEffect } from "react";
import {
  FaMobileAlt,
  FaLaptop,
  FaTv,
  FaWifi,
  FaRegQuestionCircle,
  FaBan,
  FaEdit,
  FaSave,
  FaTimes,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";
import { useAuth } from "../context/AuthContext";
import { blockedDevicesAPI, deviceGroupsAPI } from "../constants/api";

const iconMap = {
  FaMobileAlt: FaMobileAlt,
  FaLaptop: FaLaptop,
  FaTv: FaTv,
  FaWifi: FaWifi,
  BsRouter: BsRouter,
};

const DeviceCard = ({ device, onDeviceBlocked, onImmediateBlockUpdate, isBlocked = false, canBeBlocked = true }) => {
  const { routerId } = useAuth();
  const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedHostname, setEditedHostname] = useState("");
  
  // Groups state only (simplified)
  const [groups, setGroups] = useState([]);
  
  // Local blocking state for eager updates
  const [localIsBlocked, setLocalIsBlocked] = useState(isBlocked);

  // Check if this device is a router
  const isRouter = device.icon === "BsRouter";

  // Update local blocking state when prop changes
  useEffect(() => {
    setLocalIsBlocked(isBlocked);
  }, [isBlocked]);

  // Check if device is in ANY group (simplified - no need to check rules)
  const isDeviceInAnyGroup = () => {
    console.log(`🔍 [DeviceCard] Checking if device ${device.ip} (${device.mac}) is in any group...`);
    console.log(`🔍 [DeviceCard] Available groups:`, groups);
    
    const result = groups.some(group => {
      console.log(`🔍 [DeviceCard] Checking group "${group.name}" (${group.id}) with ${group.devices?.length || 0} devices`);
      
      // Check if device is in this group (by IP or MAC)
      const deviceInGroup = group.devices?.some(groupDevice => {
        const ipMatch = groupDevice.ip === device.ip;
        const macMatch = groupDevice.mac && device.mac && groupDevice.mac.toLowerCase() === device.mac.toLowerCase();
        
        console.log(`🔍 [DeviceCard] Comparing with group device:`, {
          groupDevice: { ip: groupDevice.ip, mac: groupDevice.mac },
          currentDevice: { ip: device.ip, mac: device.mac },
          ipMatch,
          macMatch
        });
        
        return ipMatch || macMatch;
      }) || false;
      
      // Debug logging for device matching
      if (deviceInGroup) {
        console.log(`🔍 [DeviceCard] Device ${device.ip} (${device.mac}) found in group "${group.name}" (${group.id})`);
      }
      
      return deviceInGroup;
    });
    
    console.log(`🔍 [DeviceCard] Device ${device.ip} (${device.mac}) is in any group: ${result}`);
    return result;
  };

  // Load groups data (simplified - no need to load rules)
  useEffect(() => {
    const loadGroups = async () => {
      if (!routerId || !device.ip || !device.mac) return;
      
      try {
        // Clear any cached group data to force fresh load
        if (routerId) {
          localStorage.removeItem(`guests_group_info_${routerId}`);
          console.log(`🧹 [DeviceCard] Cleared cached group data for router ${routerId}`);
        }
        
        // Load groups only
        const groupsResponse = await deviceGroupsAPI.getGroups(routerId);
        if (groupsResponse.success) {
          const groupsData = groupsResponse.data || [];
          setGroups(groupsData);
          
          // Debug logging with detailed group info
          console.log("✅ [DeviceCard] Groups data loaded:", {
            groupsCount: groupsData.length,
            deviceInfo: { ip: device.ip, mac: device.mac },
            groups: groupsData.map(g => ({
              id: g.id,
              name: g.name,
              deviceCount: g.devices?.length || 0,
              devices: g.devices?.map(d => ({ id: d.id, ip: d.ip, mac: d.mac })) || []
            }))
          });
        }
        
      } catch (error) {
        console.error('Error loading groups:', error);
        setGroups([]);
      }
    };
    
    loadGroups();
  }, [routerId, device.ip, device.mac]);

  // Get custom hostname from localStorage or use original
  const getDisplayHostname = () => {
    const customHostnames = JSON.parse(localStorage.getItem("customHostnames") || "{}");
    const deviceKey = `${device.ip}_${device.mac}`;
    return customHostnames[deviceKey] || device.hostname;
  };

  const displayHostname = getDisplayHostname();

  const handleStartEdit = () => {
    setIsEditing(true);
    setEditedHostname(displayHostname);
    setActionMessage(null);
  };

  const handleSaveEdit = () => {
    if (editedHostname.trim() === "") {
      setActionMessage("Hostname cannot be empty");
      return;
    }

    const customHostnames = JSON.parse(localStorage.getItem("customHostnames") || "{}");
    const deviceKey = `${device.ip}_${device.mac}`;
    
    if (editedHostname.trim() === device.hostname) {
      // If editing back to original, remove from custom hostnames
      delete customHostnames[deviceKey];
    } else {
      // Save custom hostname
      customHostnames[deviceKey] = editedHostname.trim();
    }
    
    localStorage.setItem("customHostnames", JSON.stringify(customHostnames));
    
    setIsEditing(false);
    setActionMessage("Hostname updated successfully");
    
    // Clear message after 3 seconds
    setTimeout(() => setActionMessage(null), 3000);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedHostname("");
    setActionMessage(null);
  };

  const handleAction = async (action) => {
    // Don't allow actions on router devices
    if (isRouter) {
      setActionMessage("Actions cannot be performed on router devices.");
      return;
    }

    if (!routerId) {
      setActionMessage("Router ID not configured. Please set it in Settings.");
      return;
    }

    // Store original state for potential revert
    const originalBlockedState = localIsBlocked;
    
    // Eager update - immediately change UI
    if (action === 'block') {
      setLocalIsBlocked(true);
      setActionMessage("Blocking device...");
      // Notify parent component for immediate UI update
      if (onImmediateBlockUpdate) {
        onImmediateBlockUpdate(device, true);
      }
    } else if (action === 'unblock') {
      setLocalIsBlocked(false);
      setActionMessage("Unblocking device...");
      // Notify parent component for immediate UI update
      if (onImmediateBlockUpdate) {
        onImmediateBlockUpdate(device, false);
      }
    }

    setLoading(true);
    
    try {
      if (action === 'block') {
        const response = await blockedDevicesAPI.blockDevice(routerId, {
          device_ip: device.ip,
          device_mac: device.mac
        });

        if (response.success) {
          setActionMessage("Device successfully blocked.");
          // Call callback to refresh blocked devices list
          if (onDeviceBlocked) {
            onDeviceBlocked();
          }
        } else {
          // Revert on failure
          setLocalIsBlocked(originalBlockedState);
          throw new Error(response.error || "Failed to block device");
        }
      } else if (action === 'unblock') {
        // Find the blocked device record to get the ID
        const response = await blockedDevicesAPI.getBlockedDevices(routerId);
        if (response.success) {
          const blockedDevice = response.data.find(b => 
            b.device_ip === device.ip || 
            (b.device_mac && device.mac && b.device_mac.toLowerCase() === device.mac.toLowerCase())
          );
          
          if (blockedDevice) {
            const unblockResponse = await blockedDevicesAPI.unblockDevice(routerId, blockedDevice.id);
            if (unblockResponse.success) {
              setActionMessage("Device successfully unblocked.");
              // Call callback to refresh blocked devices list
              if (onDeviceBlocked) {
                onDeviceBlocked();
              }
            } else {
              // Revert on failure
              setLocalIsBlocked(originalBlockedState);
              throw new Error(unblockResponse.error || "Failed to unblock device");
            }
          } else {
            // Revert on failure
            setLocalIsBlocked(originalBlockedState);
            throw new Error("Blocked device record not found");
          }
        } else {
          // Revert on failure
          setLocalIsBlocked(originalBlockedState);
          throw new Error("Failed to get blocked devices");
        }
      }
    } catch (err) {
      // Revert on any error
      setLocalIsBlocked(originalBlockedState);
      setActionMessage(`Failed to ${action} device: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-700 shadow-lg rounded-2xl p-5 flex flex-col items-center gap-3 w-72">
      <div className="text-5xl text-blue-500">
        <IconComponent />
      </div>

      {/* Hostname with edit functionality */}
      <div className="flex items-center gap-2 w-full justify-center">
        {isEditing ? (
          <div className="flex items-center gap-2 w-full">
            <input
              type="text"
              value={editedHostname}
              onChange={(e) => setEditedHostname(e.target.value)}
              className="text-lg font-semibold text-gray-900 dark:text-white bg-transparent border-b-2 border-blue-500 focus:outline-none flex-1 text-center"
              autoFocus
            />
            <button
              onClick={handleSaveEdit}
              className="text-green-500 hover:text-green-600 p-1"
              title="Save"
            >
              <FaSave size={14} />
            </button>
            <button
              onClick={handleCancelEdit}
              className="text-red-500 hover:text-red-600 p-1"
              title="Cancel"
            >
              <FaTimes size={14} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white text-center">
              {displayHostname}
            </h3>
            <button
              onClick={handleStartEdit}
              className="text-gray-500 hover:text-blue-500 p-1"
              title="Edit hostname"
            >
              <FaEdit size={14} />
            </button>
          </div>
        )}
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-300">
        IP: {device.ip}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        MAC: {device.mac}
      </p>

      {/* Group Rules Check Indicator */}
      {/* Removed loading indicator as per edit hint */}

      {/* Action Buttons */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => handleAction(localIsBlocked ? 'unblock' : 'block')}
          disabled={loading || isRouter || isDeviceInAnyGroup()}
          className={`p-2 rounded-full shadow-md transition flex items-center gap-1 ${
            isRouter 
              ? "bg-gray-400 text-gray-600 cursor-not-allowed" 
              : isDeviceInAnyGroup()
              ? "bg-gray-400 text-gray-600 cursor-not-allowed"
              : localIsBlocked
              ? "bg-green-500 text-white hover:bg-green-600"
              : "bg-red-500 text-white hover:bg-red-600"
          }`}
          title={
            isRouter 
              ? "Cannot block router device" 
              : isDeviceInAnyGroup() 
              ? "Cannot block device in group - Device is currently a member of a group and cannot be blocked while in that group. Remove the device from the group first to enable blocking."
              : localIsBlocked 
              ? "Unblock Device" 
              : "Block Device"
          }
        >
          <FaBan size={16} />
          <span className="text-xs">
            {isRouter 
              ? 'Cannot Block' 
              : isDeviceInAnyGroup() 
              ? 'Cannot Block' 
              : localIsBlocked 
              ? 'Unblock' 
              : 'Block'
            }
          </span>
        </button>
      </div>

      {/* Status message */}
      {actionMessage && (
        <p
          className={`text-sm text-center mt-2 ${
            /error|fail|failed|cannot|empty/i.test(actionMessage)
              ? "text-red-500 dark:text-red-400"
              : "text-green-500 dark:text-green-400"
          }`}
        >
          {actionMessage}
        </p>
      )}
    </div>
  );
};

export default DeviceCard;
