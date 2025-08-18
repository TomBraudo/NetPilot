import React, { useState, useEffect } from "react";
// Database Integration Complete:
// - Device groups are now saved to and loaded from the database
// - Device management operations use backend APIs
// - Loading states and error handling for database operations
import {
  FaPlus,
  FaTimes,
  FaEdit,
  FaTrash,
  FaUsers,
  FaTv,
  FaGamepad,
  FaShieldAlt,
  FaShoppingCart,
  FaCog,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";
import {
  FaLaptop,
  FaMobileAlt,
  FaRegQuestionCircle,
} from "react-icons/fa";
import { deviceGroupsAPI, devicesAPI, bandwidthRulesAPI, contentControlRulesAPI } from "../../constants/api";
import { useAuth } from "../../context/AuthContext.jsx";
import GroupRulesSummary from "../Components/GroupRulesSummary";

// Icon mapping
const getDeviceIcon = (deviceType) => {
  // Map device types to appropriate icons
  let iconName = 'FaLaptop'; // default
  
  if (deviceType) {
    const type = deviceType.toLowerCase();
    if (type.includes('router') || type.includes('gateway')) {
      iconName = 'BsRouter';
    } else if (type.includes('mobile') || type.includes('phone') || type.includes('android') || type.includes('ios')) {
      iconName = 'FaMobileAlt';
    } else if (type.includes('tv') || type.includes('smart tv') || type.includes('streaming')) {
      iconName = 'FaTv';
    } else if (type.includes('laptop') || type.includes('desktop') || type.includes('computer') || type.includes('pc')) {
      iconName = 'FaLaptop';
    }
  }
  
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
  const { routerId } = useAuth();
  const [devices, setDevices] = useState([]);
  const [groups, setGroups] = useState([]);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedDevices, setSelectedDevices] = useState([]);
  const [showAddToGroup, setShowAddToGroup] = useState(null);
  const [editingGroupId, setEditingGroupId] = useState(null);
  const [editingGroupName, setEditingGroupName] = useState("");
  const [confirmDeleteGroup, setConfirmDeleteGroup] = useState(null); // { id, name }
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [groupActionLoading, setGroupActionLoading] = useState({}); // { groupId: 'action' }
  const [editingDeviceId, setEditingDeviceId] = useState(null);
  const [editingDeviceName, setEditingDeviceName] = useState("");
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [confirmRemoveDevice, setConfirmRemoveDevice] = useState(null); // { groupId, groupName, deviceId, deviceName }

  // Rules state
  const [bandwidthRules, setBandwidthRules] = useState({}); // { groupId: { download_limit_mbps, upload_limit_mbps, is_active, description } }
  const [contentControlRules, setContentControlRules] = useState({}); // { groupId: { blocked_categories, is_active, description } }
  const [rulesLoading, setRulesLoading] = useState(false);
  const [rulesError, setRulesError] = useState(null);
  const [contentCategories, setContentCategories] = useState([]);

  // Load devices and groups on component mount
  useEffect(() => {
    loadDevices();
    loadGroups();
    loadContentCategories();
  }, [routerId]);

  // Load rules data when groups change
  useEffect(() => {
    if (groups.length > 0) {
      loadRulesData();
    }
  }, [groups, routerId]);

  const loadDevices = async () => {
    setDevicesLoading(true);
    try {
      const response = await devicesAPI.getDevices(routerId);
      if (response.success) {
        console.log('Loaded devices:', response.data);
        setDevices(response.data || []);
      }
    } catch (error) {
      console.error('Error loading devices:', error);
    } finally {
      setDevicesLoading(false);
    }
  };

  const reloadDevices = async () => {
    try {
      const response = await devicesAPI.getDevices(routerId);
      if (response.success) {
        setDevices(response.data || []);
      }
    } catch (error) {
      console.error('Error reloading devices:', error);
    }
  };

  const handleUpdateDevice = async (deviceId, updates) => {
    console.log('Updating device:', deviceId, 'with updates:', updates);
    
    try {
      const response = await devicesAPI.updateDevice(deviceId, routerId, updates);
      console.log('Update response:', response);
      
      if (response.success) {
        console.log('Device updated successfully, reloading devices...');
        await reloadDevices(); // Reload devices to get updated data
        return response;
      } else {
        console.error('Device update failed:', response);
        return response;
      }
    } catch (error) {
      console.error('Error updating device:', error);
      throw error;
    }
  };

  const handleDeleteDevice = async (deviceId) => {
    if (!window.confirm('Are you sure you want to delete this device?')) {
      return;
    }
    
    try {
      const response = await devicesAPI.deleteDevice(deviceId, routerId);
      if (response.success) {
        reloadDevices(); // Reload devices
        
        // Handle deleted groups if any - access from response.data.deleted_groups
        if (response.data && response.data.deleted_groups && response.data.deleted_groups.length > 0) {
          // Remove deleted groups from local state without reloading all groups
          setGroups(prev => prev.filter(group => !response.data.deleted_groups.includes(group.id)));
          console.log(`Automatically removed ${response.data.deleted_groups.length} empty groups after device deletion`);
        }
      }
    } catch (error) {
      console.error('Error deleting device:', error);
    }
  };

  const loadGroups = async () => {
    setGroupsLoading(true);
    try {
      const response = await deviceGroupsAPI.getGroups(routerId);
      if (response.success) {
        setGroups(response.data || []);
      }
    } catch (error) {
      console.error('Error loading groups:', error);
    } finally {
      setGroupsLoading(false);
    }
  };

  const loadRulesData = async () => {
    if (!routerId) return;
    
    setRulesLoading(true);
    setRulesError(null);
    
    try {
      // Load bandwidth rules
      const bandwidthResponse = await bandwidthRulesAPI.getAllRules(routerId);
      const bandwidthData = bandwidthResponse.data || [];
      
      // Convert to lookup object
      const bandwidthLookup = {};
      bandwidthData.forEach(rule => {
        bandwidthLookup[rule.group_id] = {
          download_limit_mbps: rule.download_limit_mbps,
          upload_limit_mbps: rule.upload_limit_mbps,
          is_active: rule.is_active,
          description: rule.description
        };
      });
      setBandwidthRules(bandwidthLookup);
      
      // Load content control rules
      const contentResponse = await contentControlRulesAPI.getAllRules(routerId);
      const contentData = contentResponse.data || [];
      
      // Convert to lookup object
      const contentLookup = {};
      contentData.forEach(rule => {
        contentLookup[rule.group_id] = {
          blocked_categories: rule.blocked_categories || [],
          is_active: rule.is_active,
          description: rule.description
        };
      });
      setContentControlRules(contentLookup);
      
      console.log("✅ [DevicesPage] Rules data loaded:", {
        bandwidth: Object.keys(bandwidthLookup).length,
        content: Object.keys(contentLookup).length
      });
      
      // Debug: Log specific rules for each group
      console.log("📊 [DevicesPage] Bandwidth rules:", bandwidthLookup);
      console.log("📊 [DevicesPage] Content rules:", contentLookup);
      
    } catch (error) {
      console.error("❌ [DevicesPage] Failed to load rules data:", error);
      setRulesError(`Failed to load rules: ${error.message}`);
      
      // Fallback to empty objects on error
      setBandwidthRules({});
      setContentControlRules({});
    } finally {
      setRulesLoading(false);
    }
  };

  const loadContentCategories = async () => {
    if (!routerId) return;
    
    try {
      // For now, we'll use the predefined categories that match the backend
      // In a future update, we could fetch these from the AGH API
      const predefinedCategories = [
        {
          id: 'social_media',
          name: 'Social Media',
          icon: FaUsers
        },
        {
          id: 'entertainment',
          name: 'Video Streaming',
          icon: FaTv
        },
        {
          id: 'gaming',
          name: 'Gaming',
          icon: FaGamepad
        },
        {
          id: 'adult_gambling',
          name: 'Adult Content',
          icon: FaShieldAlt
        },
        {
          id: 'shopping',
          name: 'Shopping',
          icon: FaShoppingCart
        },
        {
          id: 'custom',
          name: 'Custom Sites',
          icon: FaCog
        }
      ];
      
      setContentCategories(predefinedCategories);
    } catch (error) {
      console.error("❌ [DevicesPage] Failed to load content categories:", error);
      setContentCategories([]);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim() || selectedDevices.length === 0) return;
    
    setGroupActionLoading(prev => ({ ...prev, create: true }));
    try {
      const response = await deviceGroupsAPI.createGroup(routerId, {
        name: newGroupName.trim(),
        device_ids: selectedDevices.map(d => d.id)
      });
      
      if (response.success) {
        setShowCreateGroup(false);
        setNewGroupName("");
        setSelectedDevices([]);
        loadGroups();
        // Rules will be reloaded automatically via useEffect when groups change
      }
    } catch (error) {
      console.error('Error creating group:', error);
    } finally {
      setGroupActionLoading(prev => ({ ...prev, create: false }));
    }
  };

  const handleDeviceSelection = (device) => {
    setSelectedDevices(prev => {
      const isSelected = prev.some(d => d.id === device.id);
      if (isSelected) {
        return prev.filter(d => d.id !== device.id);
      } else {
        return [...prev, device];
      }
    });
  };

  const addDeviceToGroup = async (groupId, device) => {
    try {
      const response = await deviceGroupsAPI.addDeviceToGroup(routerId, groupId, device.id);
      if (response.success) {
        loadGroups();
        // Rules will be reloaded automatically via useEffect when groups change
      }
    } catch (error) {
      console.error('Error adding device to group:', error);
    }
  };

  const removeDeviceFromGroup = async (groupId, deviceId) => {
    try {
      const response = await deviceGroupsAPI.removeDeviceFromGroup(routerId, groupId, deviceId);
      if (response.success) {
        loadGroups();
        // Rules will be reloaded automatically via useEffect when groups change
      }
    } catch (error) {
      console.error('Error removing device from group:', error);
    }
  };

  // Check if a group has any rules (mirror criteria from GroupRulesSummary)
  const hasRules = (groupId) => {
    const br = bandwidthRules[groupId];
    const cr = contentControlRules[groupId];
    const hasBandwidth = !!br && (
      (br.download_limit_mbps !== null && br.download_limit_mbps !== undefined) ||
      (br.upload_limit_mbps !== null && br.upload_limit_mbps !== undefined)
    );
    const hasContent = !!cr && Array.isArray(cr.blocked_categories) && cr.blocked_categories.length > 0;
    return hasBandwidth || hasContent;
  };

  const deleteGroup = async (groupId) => {
    try {
      const response = await deviceGroupsAPI.deleteGroup(routerId, groupId);
      if (response.success) {
        loadGroups();
        // Rules will be reloaded automatically via useEffect when groups change
      }
    } catch (error) {
      console.error('Error deleting group:', error);
    }
  };

  const startRenameGroup = (group) => {
    setEditingGroupId(group.id);
    setEditingGroupName(group.name);
  };

  const saveRenameGroup = async () => {
    if (!editingGroupName.trim()) return;
    
    try {
      const response = await deviceGroupsAPI.updateGroup(routerId, editingGroupId, {
        name: editingGroupName.trim()
      });
      
      if (response.success) {
        setEditingGroupId(null);
        setEditingGroupName("");
        loadGroups();
        // Rules will be reloaded automatically via useEffect when groups change
      }
    } catch (error) {
      console.error('Error renaming group:', error);
    }
  };

  const cancelRenameGroup = () => {
    setEditingGroupId(null);
    setEditingGroupName("");
  };

  const getAvailableDevicesForGroup = (groupId) => {
    const group = groups.find(g => g.id === groupId);
    if (!group) return devices;
    
    const groupDeviceIds = group.devices.map(d => d.id);
    return devices.filter(device => !groupDeviceIds.includes(device.id));
  };

  const startEditDeviceName = (device) => {
    setEditingDeviceId(device.id);
    setEditingDeviceName(device.device_name || device.hostname || '');
  };

  const saveDeviceName = async () => {
    if (!editingDeviceName.trim()) return;
    
    console.log('Saving device name:', editingDeviceName.trim(), 'for device:', editingDeviceId);
    
    try {
      const response = await handleUpdateDevice(editingDeviceId, {
        device_name: editingDeviceName.trim()
      });
      
      console.log('Device update response:', response);
      
      if (response && response.success) {
        setEditingDeviceId(null);
        setEditingDeviceName("");
        // Reload devices to get the updated data
        await reloadDevices();
      }
    } catch (error) {
      console.error('Error saving device name:', error);
    }
  };

  const cancelEditDeviceName = () => {
    setEditingDeviceId(null);
    setEditingDeviceName("");
  };

  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Device Management
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Manage your network devices and create groups for organization
        </p>
      </div>

      {/* Device Management Section */}
      <div className="mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
                Devices ({devices.length})
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Manage your network devices. New devices are added automatically through network scanning.
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
            </div>
          </div>

          {devicesLoading ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                Loading devices...
              </p>
            </div>
          ) : devices.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No devices found. Run a network scan to discover devices.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {devices.map((device) => (
                <div
                  key={device.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-blue-500">
                          {getDeviceIcon(device.device_type || 'FaLaptop')}
                        </span>
                        <div className="flex-1">
                          {editingDeviceId === device.id ? (
                            <div className="flex items-center gap-2">
                              <input
                                value={editingDeviceName}
                                onChange={(e) => setEditingDeviceName(e.target.value)}
                                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-800 dark:text-white text-sm w-full"
                                placeholder="Device name"
                                autoFocus
                              />
                              <button
                                onClick={saveDeviceName}
                                className="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                              >
                                Save
                              </button>
                              <button
                                onClick={cancelEditDeviceName}
                                className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs hover:bg-gray-50 dark:hover:bg-gray-700"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold text-gray-800 dark:text-white text-sm">
                                {device.device_name || device.hostname || 'Unknown Device'}
                              </h3>
                              <button
                                onClick={() => startEditDeviceName(device)}
                                className="text-gray-500 hover:text-blue-600 text-xs"
                                title="Edit device name"
                              >
                                <FaEdit />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                        <div className="flex justify-between">
                          <span>IP:</span>
                          <span className="font-mono">{device.ip}</span>
                        </div>
                        {device.mac && (
                          <div className="flex justify-between">
                            <span>MAC:</span>
                            <span className="font-mono">{device.mac}</span>
                          </div>
                        )}
                        {device.hostname && device.hostname !== device.device_name && (
                          <div className="flex justify-between">
                            <span>Hostname:</span>
                            <span className="font-mono">{device.hostname}</span>
                          </div>
                        )}
                        {device.device_type && (
                          <div className="flex justify-between">
                            <span>Type:</span>
                            <span>{device.device_type}</span>
                          </div>
                        )}
                        {device.manufacturer && (
                          <div className="flex justify-between">
                            <span>Manufacturer:</span>
                            <span>{device.manufacturer}</span>
                          </div>
                        )}
                        {device.first_seen && (
                          <div className="flex justify-between">
                            <span>First seen:</span>
                            <span>{new Date(device.first_seen).toLocaleDateString()}</span>
                          </div>
                        )}
                        {device.last_seen && (
                          <div className="flex justify-between">
                            <span>Last seen:</span>
                            <span>{new Date(device.last_seen).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => handleDeleteDevice(device.id)}
                        className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 flex items-center gap-1"
                        title="Delete device"
                      >
                        <FaTrash className="text-xs" />
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>



      {/* Group Management Section */}
      <div className="mb-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">
                Groups
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Rename, add or remove devices, and delete groups
              </p>
            </div>
          </div>

          {groupsLoading ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                Loading groups...
              </p>
            </div>
          ) : rulesError ? (
            <div className="text-center py-12 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
              <p className="text-red-600 dark:text-red-400 text-lg mb-2">
                Error loading rules
              </p>
              <p className="text-red-500 dark:text-red-300 text-sm">
                {rulesError}
              </p>
            </div>
          ) : groups.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                No groups yet. Create one to get started.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {groups.map((group) => (
                <div
                  key={group.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {editingGroupId === group.id ? (
                        <div className="flex items-center gap-2 mb-2">
                          <input
                            value={editingGroupName}
                            onChange={(e) => setEditingGroupName(e.target.value)}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-800 dark:text-white w-64"
                            placeholder="Group name"
                            autoFocus
                          />
                          <button
                            onClick={saveRenameGroup}
                            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                          >
                            Save
                          </button>
                          <button
                            onClick={cancelRenameGroup}
                            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">
                            {group.name}
                          </h3>
                          <button
                            onClick={() => startRenameGroup(group)}
                            className="text-gray-500 hover:text-blue-600"
                            title="Rename group"
                          >
                            <FaEdit />
                          </button>
                        </div>
                      )}

                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                        {group.devices.length} device{group.devices.length !== 1 ? "s" : ""}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {(group.devices || []).map((device, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 rounded-full px-3 py-1"
                          >
                            <span className="text-blue-500">
                              {getDeviceIcon(device.device_type)}
                            </span>
                            <span className="text-sm text-gray-700 dark:text-gray-200">
                              {device.hostname || device.device_name} ({device.ip})
                            </span>
                            <button
                              onClick={() => {
                                if (hasRules(group.id)) {
                                  setConfirmRemoveDevice({
                                    groupId: group.id,
                                    groupName: group.name,
                                    deviceId: device.id,
                                    deviceName: device.hostname || device.device_name || 'Device'
                                  });
                                } else {
                                  removeDeviceFromGroup(group.id, device.id);
                                }
                              }}
                              className="text-red-500 hover:text-red-600"
                              title="Remove from group"
                            >
                              <FaTimes />
                            </button>
                          </div>
                        ))}
                        {group.devices.length === 0 && (
                          <span className="text-sm text-gray-500 dark:text-gray-400 italic">
                            No devices
                          </span>
                        )}
                      </div>

                      {/* Rules Summary Section */}
                      <GroupRulesSummary
                        bandwidthRules={bandwidthRules[group.id]}
                        contentControlRules={contentControlRules[group.id]}
                        contentCategories={contentCategories}
                        isLoading={rulesLoading}
                      />
                    </div>

                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => setShowAddToGroup(group.id)}
                        className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        <FaPlus /> Add device
                      </button>
                      <button
                        onClick={() => setConfirmDeleteGroup({ id: group.id, name: group.name, hasRules: hasRules(group.id) })}
                        className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
                      >
                        <FaTrash /> Delete group
                      </button>
                    </div>
                  </div>
                </div>
              ))}
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
                      selectedDevices.some((d) => d.id === device.id)
                        ? "bg-blue-50 dark:bg-blue-900/40 border-blue-300 dark:border-blue-600"
                        : "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-blue-500">
                        {getDeviceIcon(device.device_type)}
                      </div>
                      <div>
                        <span className="font-medium text-gray-800 dark:text-white">
                          {device.device_name || device.hostname}
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
                disabled={!newGroupName.trim() || selectedDevices.length === 0 || groupActionLoading.create}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
                  !newGroupName.trim() || selectedDevices.length === 0 || groupActionLoading.create
                    ? "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                }`}
              >
                {groupActionLoading.create ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </div>
                ) : (
                  "Create Group"
                )}
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
                        {getDeviceIcon(device.device_type)}
                      </div>
                      <div>
                        <span className="font-medium text-gray-800 dark:text-white">
                          {device.device_name || device.hostname}
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

      {/* Delete Group Confirmation Modal (shows rules warning when applicable) */}
      {confirmDeleteGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Delete Group</h3>
              <button
                onClick={() => setConfirmDeleteGroup(null)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>
            {confirmDeleteGroup.hasRules ? (
              <>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  This group <span className="font-semibold">{confirmDeleteGroup.name}</span> has rules applied.
                </p>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  Deleting it will remove those rules from all devices in this group. Continue?
                </p>
              </>
            ) : (
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                Are you sure you want to delete the group {" "}
                <span className="font-semibold">{confirmDeleteGroup.name}</span>? This cannot be undone.
              </p>
            )}
            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                onClick={() => setConfirmDeleteGroup(null)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
                onClick={() => {
                  deleteGroup(confirmDeleteGroup.id);
                  setConfirmDeleteGroup(null);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Remove Device when group has rules */}
      {confirmRemoveDevice && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Remove Device</h3>
              <button
                onClick={() => setConfirmRemoveDevice(null)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>
            <p className="text-gray-700 dark:text-gray-300 mb-2">
              The group <span className="font-semibold">{confirmRemoveDevice.groupName}</span> has rules applied.
            </p>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Removing <span className="font-semibold">{confirmRemoveDevice.deviceName}</span> from this group will remove those rules from the device. Continue?
            </p>
            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                onClick={() => setConfirmRemoveDevice(null)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                onClick={() => {
                  removeDeviceFromGroup(confirmRemoveDevice.groupId, confirmRemoveDevice.deviceId);
                  setConfirmRemoveDevice(null);
                }}
              >
                Accept
              </button>
            </div>
          </div>
        </div>
      )}


    </div>
  );
};

export default DevicesPage;

