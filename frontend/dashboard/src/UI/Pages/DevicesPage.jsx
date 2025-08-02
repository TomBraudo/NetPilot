import React, { useState, useEffect } from "react";
import { FaPlus, FaTimes, FaUserPlus } from "react-icons/fa";
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

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [groups, setGroups] = useState([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedDevices, setSelectedDevices] = useState([]);
  const [showAddToGroup, setShowAddToGroup] = useState(null);

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

  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Device Management
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Manage your network devices and organize them into groups
        </p>
      </div>

      {/* Device List Section */}
      <div className="mb-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
            All Devices ({devices.length})
          </h2>
          <button
            onClick={() => setShowCreateGroup(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <FaPlus className="text-sm" />
            Create Group
          </button>
        </div>

        {devices.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No devices found
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
              Scan your network to discover devices
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {devices.map((device, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center gap-2">
                  <div className="text-blue-500">
                    {getDeviceIcon(device.icon)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-800 dark:text-white text-sm truncate">
                      {device.hostname}
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 text-xs">
                      {device.ip}
                    </p>
                    <p className="text-gray-400 dark:text-gray-500 text-xs truncate">
                      {device.mac}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Groups Section */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
            Device Groups ({groups.length})
          </h2>
          <div className="flex gap-2">
            {/* Debug button - only show when there are groups */}
            {groups.length > 0 && (
              <button
                onClick={clearAllGroups}
                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm transition-colors"
                title="Clear all groups"
              >
                Clear All
              </button>
            )}
          </div>
        </div>

        {groups.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400 text-lg">
              No groups created yet
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
              Create groups to organize your devices
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groups.map((group) => (
              <div
                key={group.id}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700"
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                    {group.name}
                  </h3>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowAddToGroup(group.id)}
                      className="bg-green-500 hover:bg-green-600 text-white p-2 rounded-lg transition-colors"
                      title="Add Device"
                    >
                      <FaUserPlus className="text-sm" />
                    </button>
                    <button
                      onClick={() => deleteGroup(group.id)}
                      className="bg-red-500 hover:bg-red-600 text-white p-2 rounded-lg transition-colors"
                      title="Delete Group"
                    >
                      <FaTimes className="text-sm" />
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  {group.devices.map((device, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-blue-500">
                          {getDeviceIcon(device.icon)}
                        </div>
                        <span className="font-medium text-gray-800 dark:text-white">
                          {device.hostname}
                        </span>
                      </div>
                      <button
                        onClick={() =>
                          removeDeviceFromGroup(group.id, device.ip)
                        }
                        className="text-red-500 hover:text-red-700 dark:hover:text-red-400 p-1 transition-colors"
                        title="Remove from group"
                      >
                        <FaTimes className="text-sm" />
                      </button>
                    </div>
                  ))}

                  {group.devices.length === 0 && (
                    <p className="text-gray-400 dark:text-gray-500 text-center py-4">
                      No devices in this group
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
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
    </div>
  );
};

export default DevicesPage;
