import React, { useState, useEffect } from "react";
import {
  FaPlus,
  FaTimes,
  FaUserPlus,
  FaGlobe,
  FaGamepad,
  FaShoppingCart,
  FaNewspaper,
  FaCog,
  FaUsers,
  FaEye,
  FaEyeSlash,
  FaCheck,
  FaDownload,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";
import {
  FaLaptop,
  FaMobileAlt,
  FaTv,
  FaRegQuestionCircle,
} from "react-icons/fa";

// Icon mapping
const getDeviceIcon = (iconName) => {
  const iconMap = {
    BsRouter: BsRouter,
    FaLaptop: FaLaptop,
    FaMobileAlt: FaMobileAlt,
    FaTv: FaTv,
    FaRegQuestionCircle: FaRegQuestionCircle,
  };
  const IconComponent = iconMap[iconName] || FaRegQuestionCircle;
  return <IconComponent className="text-2xl" />;
};

// Custom 18+ Icon Component
const EighteenPlusIcon = ({ className }) => (
  <div className={`flex items-center justify-center ${className}`}>
    <span className="font-bold text-sm">18+</span>
  </div>
);

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [groups, setGroups] = useState([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedDevices, setSelectedDevices] = useState([]);
  const [showAddToGroup, setShowAddToGroup] = useState(null);

  // Content Controls State
  const [selectedGroups, setSelectedGroups] = useState([]);
  const [contentCategories, setContentCategories] = useState([
    {
      id: "social",
      name: "Social Media",
      icon: FaUsers,
      blocked: false,
      sites: 12,
      description: "Facebook, Instagram, Twitter, TikTok",
    },
    {
      id: "video",
      name: "Video Streaming",
      icon: FaTv,
      blocked: false,
      sites: 8,
      description: "YouTube, Netflix, Twitch, Disney+",
    },
    {
      id: "gaming",
      name: "Gaming",
      icon: FaGamepad,
      blocked: false,
      sites: 15,
      description: "Steam, Epic Games, gaming platforms",
    },
    {
      id: "adult",
      name: "Adult Content",
      icon: EighteenPlusIcon,
      blocked: true,
      sites: 1000,
      description: "Adult and explicit content sites",
    },
    {
      id: "shopping",
      name: "Shopping",
      icon: FaShoppingCart,
      blocked: false,
      sites: 25,
      description: "Amazon, eBay, retail websites",
    },
    {
      id: "custom",
      name: "Custom Sites",
      icon: FaCog,
      blocked: false,
      sites: 5,
      description: "User-defined blocked sites",
    },
  ]);
  const [hasContentChanges, setHasContentChanges] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [showAddUrlModal, setShowAddUrlModal] = useState(null);
  const [newUrl, setNewUrl] = useState("");
  const [customUrls, setCustomUrls] = useState({});

  // Bandwidth Limits State (download only)
  const [bandwidthGroups, setBandwidthGroups] = useState([]);
  const [bandwidthChanges, setBandwidthChanges] = useState({});
  const [bulkValues, setBulkValues] = useState({ downLimit: "" });
  const [errors, setErrors] = useState({});

  // Helper functions for localStorage operations
  const saveGroupsToStorage = (groupsToSave) => {
    try {
      localStorage.setItem("deviceGroups", JSON.stringify(groupsToSave));
      console.log("Groups successfully saved to localStorage");
    } catch (error) {
      console.error("Failed to save groups to localStorage:", error);
    }
  };

  const loadGroupsFromStorage = () => {
    try {
      const savedGroups = localStorage.getItem("deviceGroups");
      return savedGroups ? JSON.parse(savedGroups) : [];
    } catch (error) {
      console.error("Failed to load groups from localStorage:", error);
      return [];
    }
  };

  const loadDevicesFromStorage = () => {
    try {
      const savedDevices = localStorage.getItem("scannedDevices");
      return savedDevices ? JSON.parse(savedDevices) : [];
    } catch (error) {
      console.error("Failed to load devices from localStorage:", error);
      return [];
    }
  };

  // Load data from localStorage on component mount
  useEffect(() => {
    const loadedDevices = loadDevicesFromStorage();
    const loadedGroups = loadGroupsFromStorage();

    setDevices(loadedDevices);
    setGroups(loadedGroups);

    console.log(
      "Loaded from localStorage - Devices:",
      loadedDevices.length,
      "Groups:",
      loadedGroups.length
    );
  }, []);

  // Save groups to localStorage whenever groups change
  useEffect(() => {
    if (groups.length > 0) {
      saveGroupsToStorage(groups);
    }
  }, [groups]);

  // Listen for device updates from localStorage (when new scan is done)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "scannedDevices") {
        try {
          const newDevices = e.newValue ? JSON.parse(e.newValue) : [];
          setDevices(newDevices);
        } catch (error) {
          console.error("Error parsing updated devices:", error);
        }
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const handleCreateGroup = () => {
    if (newGroupName.trim() && selectedDevices.length > 0) {
      const newGroup = {
        id: Date.now(),
        name: newGroupName.trim(),
        devices: selectedDevices,
        createdAt: new Date().toISOString(),
      };

      const updatedGroups = [...groups, newGroup];
      setGroups(updatedGroups);

      // Immediately save to localStorage
      saveGroupsToStorage(updatedGroups);

      // Reset form
      setNewGroupName("");
      setSelectedDevices([]);
      setShowCreateGroup(false);

      console.log(
        "New group created:",
        newGroup.name,
        "with",
        newGroup.devices.length,
        "devices"
      );
    }
  };

  const handleDeviceSelection = (device) => {
    setSelectedDevices((prev) => {
      const isSelected = prev.some((d) => d.ip === device.ip);
      if (isSelected) {
        return prev.filter((d) => d.ip !== device.ip);
      } else {
        return [...prev, device];
      }
    });
  };

  const removeDeviceFromGroup = (groupId, deviceIp) => {
    setGroups((prev) =>
      prev.map((group) => {
        if (group.id === groupId) {
          return {
            ...group,
            devices: group.devices.filter((device) => device.ip !== deviceIp),
          };
        }
        return group;
      })
    );
  };

  const addDeviceToGroup = (groupId, device) => {
    setGroups((prev) =>
      prev.map((group) => {
        if (group.id === groupId) {
          const deviceExists = group.devices.some((d) => d.ip === device.ip);
          if (!deviceExists) {
            return {
              ...group,
              devices: [...group.devices, device],
            };
          }
        }
        return group;
      })
    );
  };

  const getAvailableDevicesForGroup = (groupId) => {
    const group = groups.find((g) => g.id === groupId);
    if (!group) return devices;

    return devices.filter(
      (device) =>
        !group.devices.some((groupDevice) => groupDevice.ip === device.ip)
    );
  };

  const deleteGroup = (groupId) => {
    const groupToDelete = groups.find((g) => g.id === groupId);
    const updatedGroups = groups.filter((group) => group.id !== groupId);

    setGroups(updatedGroups);
    saveGroupsToStorage(updatedGroups);

    console.log("Group deleted:", groupToDelete?.name);
  };

  // Debug function to clear all groups
  const clearAllGroups = () => {
    setGroups([]);
    localStorage.removeItem("deviceGroups");
    console.log("All groups cleared");
  };

  // Content Controls Handlers
  const handleContentToggle = (categoryId) => {
    setContentCategories((prev) =>
      prev.map((cat) =>
        cat.id === categoryId ? { ...cat, blocked: !cat.blocked } : cat
      )
    );
    setHasContentChanges(true);
  };

  const handleGroupSelection = (groupId) => {
    setSelectedGroups((prev) => {
      const isSelected = prev.includes(groupId);
      return isSelected
        ? prev.filter((id) => id !== groupId)
        : [...prev, groupId];
    });
    setHasContentChanges(true);
  };

  const handleApplyContentChanges = async () => {
    if (selectedGroups.length === 0) {
      alert("Please select at least one group to apply changes to.");
      return;
    }

    setContentLoading(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      setHasContentChanges(false);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);

      console.log("Content controls applied to groups:", selectedGroups);
      console.log(
        "Active blocks:",
        contentCategories.filter((cat) => cat.blocked)
      );
    } catch (error) {
      console.error("Failed to apply content changes:", error);
      alert("Failed to apply changes. Please try again.");
    } finally {
      setContentLoading(false);
    }
  };

  // URL Management Handlers
  const handleAddUrl = (categoryId) => {
    if (newUrl.trim()) {
      setCustomUrls((prev) => ({
        ...prev,
        [categoryId]: [...(prev[categoryId] || []), newUrl.trim()],
      }));
      setNewUrl("");
      setShowAddUrlModal(null);
      setHasContentChanges(true);
    }
  };

  const handleRemoveUrl = (categoryId, urlIndex) => {
    setCustomUrls((prev) => ({
      ...prev,
      [categoryId]: prev[categoryId].filter((_, index) => index !== urlIndex),
    }));
    setHasContentChanges(true);
  };

  // Bandwidth Limits Handlers
  const handleBandwidthChange = (groupId, field, value) => {
    setBandwidthChanges((prev) => ({
      ...prev,
      [groupId]: {
        ...prev[groupId],
        [field]: value,
      },
    }));

    // Clear error for this field
    if (errors[`${groupId}_${field}`]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[`${groupId}_${field}`];
        return newErrors;
      });
    }
  };

  const validateBandwidth = (value) => {
    if (!value || value === "") return null; // Allow empty values
    const num = parseFloat(value);
    if (isNaN(num) || num < 0.1 || num > 1000) {
      return "Must be between 0.1 and 1000 Mbps";
    }
    return null;
  };

  const handleBandwidthToggle = (groupId) => {
    setBandwidthGroups((prev) =>
      prev.map((group) =>
        group.id === groupId ? { ...group, enabled: !group.enabled } : group
      )
    );
  };

  const handleApplyBandwidth = async (groupId) => {
    const changes = bandwidthChanges[groupId];
    if (!changes) return;

    // Validate inputs
    const newErrors = {};
    if (changes.downLimit !== undefined && changes.downLimit !== "") {
      const error = validateBandwidth(changes.downLimit);
      if (error) newErrors[`${groupId}_downLimit`] = error;
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors((prev) => ({ ...prev, ...newErrors }));
      return;
    }

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Update bandwidth groups with new values
      setBandwidthGroups((prev) =>
        prev.map((group) =>
          group.id === groupId
            ? {
                ...group,
                downLimit:
                  changes.downLimit !== undefined
                    ? changes.downLimit === ""
                      ? ""
                      : parseFloat(changes.downLimit)
                    : group.downLimit,
              }
            : group
        )
      );

      // Clear changes for this group
      setBandwidthChanges((prev) => {
        const newChanges = { ...prev };
        delete newChanges[groupId];
        return newChanges;
      });

      console.log("Bandwidth limits applied for group:", groupId, changes);
    } catch (error) {
      console.error("Failed to apply bandwidth changes:", error);
      alert("Failed to apply changes. Please try again.");
    }
  };

  const handleBulkApply = async () => {
    const downError = bulkValues.downLimit
      ? validateBandwidth(bulkValues.downLimit)
      : null;

    if (downError) {
      setErrors({
        bulk_downLimit: downError,
      });
      return;
    }

    if (!bulkValues.downLimit) {
      alert("Please enter a download bandwidth limit to apply.");
      return;
    }

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Apply to all groups
      setBandwidthGroups((prev) =>
        prev.map((group) => ({
          ...group,
          downLimit: bulkValues.downLimit
            ? parseFloat(bulkValues.downLimit)
            : group.downLimit,
        }))
      );

      setBulkValues({ downLimit: "" });
      setErrors({});

      console.log("Bulk bandwidth limits applied:", bulkValues);
    } catch (error) {
      console.error("Failed to apply bulk changes:", error);
      alert("Failed to apply changes. Please try again.");
    }
  };

  // Initialize bandwidth groups from device groups
  useEffect(() => {
    const bandwidthData = groups.map((group) => ({
      id: group.id,
      name: group.name,
      deviceCount: group.devices.length,
      downLimit: "", // No default limit
      enabled: false, // Disabled by default
    }));
    setBandwidthGroups(bandwidthData);
  }, [groups]);

  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Device Management
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Manage your network devices, create groups, and set content and
          bandwidth controls
        </p>
      </div>

      {/* Create Group Section - Small */}
      <div className="mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
                Quick Actions
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Create groups and manage devices
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreateGroup(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                <FaPlus className="text-sm" />
                Create Group
              </button>
              <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center">
                {devices.length} devices • {groups.length} groups
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bandwidth Limits Section */}
      <div className="mb-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
                Bandwidth Limits
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Set download speed limits for device groups
              </p>
            </div>
          </div>

          {/* Bulk Apply Section */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-medium text-gray-800 dark:text-white mb-4">
              Bulk Apply Limits
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Download Limit (Mbps)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="1000"
                  step="0.1"
                  value={bulkValues.downLimit}
                  onChange={(e) =>
                    setBulkValues((prev) => ({
                      ...prev,
                      downLimit: e.target.value,
                    }))
                  }
                  className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white ${
                    errors.bulk_downLimit
                      ? "border-red-300"
                      : "border-gray-300 dark:border-gray-600"
                  }`}
                  placeholder="e.g., 50"
                />
                {errors.bulk_downLimit && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.bulk_downLimit}
                  </p>
                )}
              </div>
              <button
                onClick={handleBulkApply}
                className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg transition-colors"
              >
                Apply to All Groups
              </button>
            </div>
          </div>

          {/* Groups Table */}
          {bandwidthGroups.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border border-gray-200 dark:border-gray-700 rounded-lg">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      Group
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      Devices
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      Download Limit
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      Enabled
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {bandwidthGroups.map((group) => {
                    const changes = bandwidthChanges[group.id] || {};
                    const hasChanges = Object.keys(changes).length > 0;

                    return (
                      <tr
                        key={group.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <FaUsers className="text-blue-500" />
                            <span className="font-medium text-gray-800 dark:text-white">
                              {group.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-300">
                          {group.deviceCount} devices
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              min="0.1"
                              max="1000"
                              step="0.1"
                              value={
                                changes.downLimit !== undefined
                                  ? changes.downLimit
                                  : group.downLimit || ""
                              }
                              onChange={(e) =>
                                handleBandwidthChange(
                                  group.id,
                                  "downLimit",
                                  e.target.value
                                )
                              }
                              className={`w-20 p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white text-sm ${
                                errors[`${group.id}_downLimit`]
                                  ? "border-red-300"
                                  : "border-gray-300 dark:border-gray-600"
                              }`}
                              placeholder="No limit"
                            />
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              Mbps
                            </span>
                            <FaDownload className="text-green-500 text-sm" />
                          </div>
                          {errors[`${group.id}_downLimit`] && (
                            <p className="text-red-500 text-xs mt-1">
                              {errors[`${group.id}_downLimit`]}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={group.enabled}
                              onChange={() => handleBandwidthToggle(group.id)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 dark:after:border-gray-500 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 dark:peer-checked:bg-blue-500"></div>
                          </label>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleApplyBandwidth(group.id)}
                            disabled={!hasChanges}
                            className={`px-3 py-1 rounded text-sm transition-colors ${
                              hasChanges
                                ? "bg-blue-500 hover:bg-blue-600 text-white"
                                : "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                            }`}
                          >
                            Apply
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No device groups available
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                Create device groups first to set bandwidth limits
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create Group Modal */}
      {showCreateGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                Create New Group
              </h3>
              <button
                onClick={() => {
                  setShowCreateGroup(false);
                  setNewGroupName("");
                  setSelectedDevices([]);
                }}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Group Name
              </label>
              <input
                type="text"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-800 dark:text-white"
                placeholder="Enter group name"
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Devices ({selectedDevices.length} selected)
              </label>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {devices.map((device, index) => (
                  <div
                    key={index}
                    onClick={() => handleDeviceSelection(device)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedDevices.some((d) => d.ip === device.ip)
                        ? "bg-blue-50 dark:bg-blue-900/40 border-blue-300 dark:border-blue-600"
                        : "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-blue-500">
                        {getDeviceIcon(device.icon)}
                      </div>
                      <div>
                        <span className="font-medium text-gray-800 dark:text-white">
                          {device.hostname}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 text-sm ml-2">
                          ({device.ip})
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateGroup}
                disabled={!newGroupName.trim() || selectedDevices.length === 0}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
                  !newGroupName.trim() || selectedDevices.length === 0
                    ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                }`}
              >
                Create Group
              </button>
              <button
                onClick={() => {
                  setShowCreateGroup(false);
                  setNewGroupName("");
                  setSelectedDevices([]);
                }}
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add to Group Modal */}
      {showAddToGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-lg w-full mx-4 max-h-[70vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                Add Device to Group
              </h3>
              <button
                onClick={() => setShowAddToGroup(null)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>

            <div className="space-y-2">
              {getAvailableDevicesForGroup(showAddToGroup).map(
                (device, index) => (
                  <div
                    key={index}
                    onClick={() => {
                      addDeviceToGroup(showAddToGroup, device);
                      setShowAddToGroup(null);
                    }}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-blue-500">
                        {getDeviceIcon(device.icon)}
                      </div>
                      <div>
                        <span className="font-medium text-gray-800 dark:text-white">
                          {device.hostname}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 text-sm ml-2">
                          ({device.ip})
                        </span>
                      </div>
                    </div>
                  </div>
                )
              )}

              {getAvailableDevicesForGroup(showAddToGroup).length === 0 && (
                <p className="text-gray-400 dark:text-gray-500 text-center py-4">
                  No available devices to add
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add URL Modal */}
      {showAddUrlModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                Add Custom URL
              </h3>
              <button
                onClick={() => {
                  setShowAddUrlModal(null);
                  setNewUrl("");
                }}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Website URL
              </label>
              <input
                type="text"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                onKeyPress={(e) =>
                  e.key === "Enter" && handleAddUrl(showAddUrlModal)
                }
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-800 dark:text-white"
                placeholder="e.g., example.com"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Enter a website URL to add to this category
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => handleAddUrl(showAddUrlModal)}
                disabled={!newUrl.trim()}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
                  !newUrl.trim()
                    ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                }`}
              >
                Add URL
              </button>
              <button
                onClick={() => {
                  setShowAddUrlModal(null);
                  setNewUrl("");
                }}
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Content Controls Section */}
      <div className="mb-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
                Content Controls
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Block website categories for selected device groups
              </p>
            </div>
            {hasContentChanges && (
              <button
                onClick={handleApplyContentChanges}
                disabled={contentLoading || selectedGroups.length === 0}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                {contentLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Applying...
                  </>
                ) : (
                  <>
                    <FaCheck className="text-sm" />
                    Apply Changes
                  </>
                )}
              </button>
            )}
          </div>

          {/* Group Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Target Groups ({selectedGroups.length} selected)
            </label>
            <div className="flex flex-wrap gap-2">
              {groups.map((group) => (
                <button
                  key={group.id}
                  onClick={() => handleGroupSelection(group.id)}
                  className={`px-4 py-2 rounded-lg border transition-colors ${
                    selectedGroups.includes(group.id)
                      ? "bg-blue-500 text-white border-blue-500"
                      : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-500"
                  }`}
                >
                  <FaUsers className="inline mr-2" />
                  {group.name} ({group.devices.length})
                </button>
              ))}
              {groups.length === 0 && (
                <p className="text-gray-500 dark:text-gray-400 italic">
                  No groups available. Create groups first to use content
                  controls.
                </p>
              )}
            </div>
          </div>

          {/* Category Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {contentCategories.map((category) => {
              const IconComponent = category.icon;
              const categoryUrls = customUrls[category.id] || [];
              return (
                <div
                  key={category.id}
                  className={`border rounded-lg p-4 transition-all hover:shadow-md ${
                    category.blocked
                      ? "border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20"
                      : "border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-700"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-lg ${
                          category.blocked
                            ? "bg-red-100 text-red-600 dark:bg-red-800 dark:text-red-300"
                            : "bg-blue-100 text-blue-600 dark:bg-blue-800 dark:text-blue-300"
                        }`}
                      >
                        <IconComponent className="text-lg" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-800 dark:text-white">
                          {category.name}
                        </h3>
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            category.blocked
                              ? "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100"
                              : "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100"
                          }`}
                        >
                          {category.sites + categoryUrls.length} sites
                        </span>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={category.blocked}
                        onChange={() => handleContentToggle(category.id)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 dark:after:border-gray-500 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600 dark:peer-checked:bg-red-500"></div>
                    </label>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    {category.description}
                  </p>

                  {/* Custom URLs */}
                  {categoryUrls.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Custom URLs:
                      </p>
                      <div className="space-y-1">
                        {categoryUrls.map((url, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between bg-gray-100 dark:bg-gray-600 rounded px-2 py-1"
                          >
                            <span className="text-xs text-gray-600 dark:text-gray-300 truncate">
                              {url}
                            </span>
                            <button
                              onClick={() =>
                                handleRemoveUrl(category.id, index)
                              }
                              className="text-red-500 hover:text-red-700 ml-2"
                            >
                              <FaTimes className="text-xs" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-medium ${
                          category.blocked
                            ? "text-red-600 dark:text-red-400"
                            : "text-green-600 dark:text-green-400"
                        }`}
                      >
                        {category.blocked ? "BLOCKED" : "ALLOWED"}
                      </span>
                      {category.blocked && (
                        <FaEyeSlash className="text-red-500 text-xs" />
                      )}
                    </div>
                    <button
                      onClick={() => setShowAddUrlModal(category.id)}
                      className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      title="Add custom URL"
                    >
                      <FaPlus className="text-xs" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {selectedGroups.length === 0 && hasContentChanges && (
            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg">
              <p className="text-yellow-800 dark:text-yellow-300 text-sm">
                Please select at least one group to apply content controls to.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Success Toast */}
      {showSuccessToast && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <FaCheck />
          Content controls applied successfully!
        </div>
      )}
    </div>
  );
};

export default DevicesPage;
