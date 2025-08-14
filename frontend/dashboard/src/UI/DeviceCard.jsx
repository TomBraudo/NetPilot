import React, { useState } from "react";
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
      // Keep existing logic for block only
      const endpoint = {
        block: "http://localhost:5000/api/block",
      }[action];

      const body = { ip: device.ip, mac: device.mac };

      res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Failed to ${action} device`);

      const result = await res.json();
      if (result.success) {
        setActionMessage(`Device successfully ${action}ed.`);
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
