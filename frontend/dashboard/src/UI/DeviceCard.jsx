import React, { useState } from "react";
import {
  FaHandPaper,
  FaTachometerAlt,
  FaMobileAlt,
  FaLaptop,
  FaTv,
  FaWifi,
  FaRegQuestionCircle,
  FaShieldAlt,
  FaBan,
  FaCheck,
  FaEdit,
  FaSave,
  FaTimes,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";
import { whitelistAPI, blacklistAPI } from "../constants/api";

const iconMap = {
  FaMobileAlt: FaMobileAlt,
  FaLaptop: FaLaptop,
  FaTv: FaTv,
  FaWifi: FaWifi,
  BsRouter: BsRouter,
};

const DeviceCard = ({ device }) => {
  const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [limitValue, setLimitValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedHostname, setEditedHostname] = useState("");

  // Check if this device is a router
  const isRouter = device.icon === "BsRouter";

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

    setLoading(true);
    try {
      let res;
      if (action === 'whitelist') {
        // Use whitelist API helper with routerId
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          throw new Error('No routerId found in localStorage');
        }
        
        const result = await whitelistAPI.add(routerId, {
          ip: device.ip,
          name: displayHostname, // Use display hostname (custom or original)
          description: `${displayHostname} - ${device.mac}`
        });
        
        // Create a mock response object to maintain compatibility
        res = {
          ok: result.success,
          json: async () => result
        };
      } else if (action === 'blacklist') {
        // Use blacklist API helper with routerId
        const routerId = localStorage.getItem('routerId');
        if (!routerId) {
          throw new Error('No routerId found in localStorage');
        }
        
        const result = await blacklistAPI.add(routerId, {
          ip: device.ip,
          name: displayHostname, // Use display hostname (custom or original)
          description: `${displayHostname} - ${device.mac}`
        });
        
        // Create a mock response object to maintain compatibility
        res = {
          ok: result.success,
          json: async () => result
        };
      } else {
        // Keep existing logic for block
        const endpoint = {
          block: "http://localhost:5000/api/block"
        }[action];

        const body = { ip: device.ip, mac: device.mac };

        res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }

      if (!res.ok) throw new Error(`Failed to ${action} device`);

      const result = await res.json();
      if (result.success) {
        setActionMessage(`Device successfully ${action}ed.`);
        // Update localStorage to trigger control page refresh
        if (action === 'whitelist') {
          const event = new StorageEvent('storage', {
            key: 'whitelistUpdate',
            newValue: Date.now().toString()
          });
          window.dispatchEvent(event);
        }
      } else {
        throw new Error(result.message || `Failed to ${action} device`);
      }
    } catch (err) {
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

      {/* Action Buttons */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => handleAction('whitelist')}
          disabled={loading || isRouter}
          className={`p-2 rounded-full shadow-md transition flex items-center gap-1 ${
            isRouter 
              ? "bg-gray-400 text-gray-600 cursor-not-allowed" 
              : "bg-green-500 text-white hover:bg-green-600"
          }`}
          title={isRouter ? "Cannot whitelist router device" : "Add to Whitelist"}
        >
          <FaCheck size={16} />
          <span className="text-xs">Whitelist</span>
        </button>
        <button
          onClick={() => handleAction('blacklist')}
          disabled={loading || isRouter}
          className={`p-2 rounded-full shadow-md transition flex items-center gap-1 ${
            isRouter 
              ? "bg-gray-400 text-gray-600 cursor-not-allowed" 
              : "bg-yellow-500 text-white hover:bg-yellow-600"
          }`}
          title={isRouter ? "Cannot blacklist router device" : "Add to Blacklist"}
        >
          <FaShieldAlt size={16} />
          <span className="text-xs">Blacklist</span>
        </button>
        <button
          onClick={() => handleAction('block')}
          disabled={loading || isRouter}
          className={`p-2 rounded-full shadow-md transition flex items-center gap-1 ${
            isRouter 
              ? "bg-gray-400 text-gray-600 cursor-not-allowed" 
              : "bg-red-500 text-white hover:bg-red-600"
          }`}
          title={isRouter ? "Cannot block router device" : "Block Device"}
        >
          <FaBan size={16} />
          <span className="text-xs">Block</span>
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
