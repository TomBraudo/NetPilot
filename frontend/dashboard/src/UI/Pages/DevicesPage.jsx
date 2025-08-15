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
  FaEdit,
  FaTrash,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";
import {
  FaLaptop,
  FaMobileAlt,
  FaTv,
  FaRegQuestionCircle,
} from "react-icons/fa";
import { aghAPI, bandwidthAPI, deviceGroupsAPI, devicesAPI } from "../../constants/api";
import { useAuth } from "../../context/AuthContext.jsx";

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

  // Content Controls State
  const [selectedGroups, setSelectedGroups] = useState([]);
  const [contentCategories, setContentCategories] = useState([
    {
      id: "social_media",
      name: "Social Media",
      icon: FaUsers,
      blocked: false,
      sites: 12,
      description: "Facebook, Instagram, Twitter, TikTok",
    },
    {
      id: "entertainment",
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
      id: "adult_gambling",
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
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [categoriesError, setCategoriesError] = useState(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [showAddUrlModal, setShowAddUrlModal] = useState(null);
  const [newUrl, setNewUrl] = useState("");
  const [customUrls, setCustomUrls] = useState({});
  const [domainsModal, setDomainsModal] = useState(null); // { categoryId, name, domains: [] }

  // Bandwidth Limits State (download only)
  const [bandwidthGroups, setBandwidthGroups] = useState([]);
  const [bandwidthChanges, setBandwidthChanges] = useState({});
  const [bulkValues, setBulkValues] = useState({ downLimit: "" });
  const [errors, setErrors] = useState({});
  const [globalLimits, setGlobalLimits] = useState({ dlMbps: "", ulMbps: "", lanCidr: "" });
  const [globalLoading, setGlobalLoading] = useState(false);

  // Helper function to map backend device format to frontend format
  const mapBackendDeviceToFrontend = (backendDevice) => {
    return {
      id: backendDevice.id,
      ip: backendDevice.ip,
      mac: backendDevice.mac,
      hostname: backendDevice.hostname || backendDevice.device_name || 'Unknown Device',
      icon: getDeviceTypeIcon(backendDevice.device_type),
      type: backendDevice.device_type || 'Unknown'
    };
  };

  const getDeviceTypeIcon = (deviceType) => {
    const typeMap = {
      'router': 'BsRouter',
      'laptop': 'FaLaptop',
      'phone': 'FaMobileAlt',
      'mobile': 'FaMobileAlt',
      'tv': 'FaTv',
      'television': 'FaTv'
    };
    return typeMap[deviceType?.toLowerCase()] || 'FaRegQuestionCircle';
  };

  // Helper function to check if an ID is a UUID


  // API helper functions
  const loadGroupsFromBackend = async () => {
    if (!routerId) return [];
    
    const response = await deviceGroupsAPI.getGroups(routerId);
    const backendGroups = response.data || [];
    
    // Map backend format to frontend format
    return backendGroups.map(group => ({
      id: group.id,
      name: group.name,
      description: group.description,
      devices: (group.devices || []).map(mapBackendDeviceToFrontend),
      createdAt: group.created_at
    }));
  };



  // Load data from backend
  useEffect(() => {
    const loadData = async () => {
      setGroupsLoading(true);
      
      try {
        // Load devices from backend first
        let loadedDevices = [];
        try {
          const devicesResponse = await devicesAPI.getAll(routerId);
          const backendDevices = devicesResponse.data || [];
          loadedDevices = backendDevices.map(mapBackendDeviceToFrontend);
          console.log("Loaded devices from backend:", loadedDevices.length);
        } catch (deviceError) {
          console.warn("Failed to load devices from backend, checking localStorage:", deviceError);
          // FOR NOW: Fallback to localStorage for devices (as requested by user)
          const savedDevices = localStorage.getItem("scannedDevices");
          if (savedDevices) {
            loadedDevices = JSON.parse(savedDevices);
            console.log("Loaded devices from localStorage:", loadedDevices.length);
          }
        }
        setDevices(loadedDevices);

        // Load groups from backend (no fallback for groups)
        const loadedGroups = await loadGroupsFromBackend();
        setGroups(loadedGroups);
        console.log("Loaded groups from backend:", loadedGroups.length);
      } catch (error) {
        console.error("Failed to load data from backend:", error);
        alert("Failed to load data from server. Please check your connection and try again.");
      } finally {
        setGroupsLoading(false);
      }
    };

    if (routerId) {
      loadData();
    }
  }, [routerId]);

  // (Optional) Could load AGH categories dynamically, but keep default UI categories as requested





  const handleCreateGroup = async () => {
    if (!newGroupName.trim() || selectedDevices.length === 0) return;

    setGroupActionLoading(prev => ({ ...prev, create: true }));
    try {
      // Validate devices against database instead of local objects
      console.log("🔍 Validating devices against database:", selectedDevices.length, "devices selected");
      
      const deviceIdentifiers = selectedDevices.map(device => device.id || device.ip);
      console.log("📋 Device identifiers to validate:", deviceIdentifiers);
      
      const validationResult = await devicesAPI.validateDevices(routerId, deviceIdentifiers);
      console.log("✅ Database validation result:", validationResult);
      
      if (validationResult.data.total_invalid > 0) {
        const invalidCount = validationResult.data.total_invalid;
        const validCount = validationResult.data.total_valid;
        console.warn(`⚠️ ${invalidCount} device(s) not found in database, ${validCount} valid`);
        alert(`Cannot create group: ${invalidCount} device(s) don't exist in the database. Please scan for devices first or use only devices that were previously saved to the backend.`);
        return;
      }

      const validDevices = validationResult.data.valid_devices;
      const deviceIds = validDevices.map(device => device.id);
      console.log("🎯 Using validated device IDs:", deviceIds);

      const createGroupResponse = await deviceGroupsAPI.createGroup(routerId, {
        name: newGroupName.trim(),
        description: "",
        device_ids: deviceIds
      });

      const createdGroup = createGroupResponse.data;

      // Map backend response to frontend format
      const frontendGroup = {
        id: createdGroup.id,
        name: createdGroup.name,
        description: createdGroup.description,
        devices: (createdGroup.devices || []).map(mapBackendDeviceToFrontend),
        createdAt: createdGroup.created_at
      };

      const updatedGroups = [...groups, frontendGroup];
      setGroups(updatedGroups);

      // Reset form
      setNewGroupName("");
      setSelectedDevices([]);
      setShowCreateGroup(false);

      console.log("Group created via backend:", frontendGroup.name);
    } catch (error) {
      console.error("Failed to create group:", error);
      alert("Failed to create group: " + error.message);
    } finally {
      setGroupActionLoading(prev => ({ ...prev, create: false }));
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

  const removeDeviceFromGroup = async (groupId, deviceIp) => {
    const group = groups.find(g => g.id === groupId);
    const deviceToRemove = group?.devices.find(d => d.ip === deviceIp);
    
    if (!deviceToRemove) return;

    try {
      await deviceGroupsAPI.removeDeviceFromGroup(routerId, groupId, deviceToRemove.id || deviceIp);
      
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

      console.log("Device removed from group via backend");
    } catch (error) {
      console.error("Failed to remove device from group:", error);
      alert("Failed to remove device from group: " + error.message);
    }
  };

  const addDeviceToGroup = async (groupId, device) => {
    try {
      await deviceGroupsAPI.addDeviceToGroup(routerId, groupId, device.id || device.ip);
      
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

      console.log("Device added to group via backend");
    } catch (error) {
      console.error("Failed to add device to group:", error);
      alert("Failed to add device to group: " + error.message);
    }
  };

  const getAvailableDevicesForGroup = (groupId) => {
    const group = groups.find((g) => g.id === groupId);
    if (!group) return devices;

    return devices.filter(
      (device) =>
        !group.devices.some((groupDevice) => groupDevice.ip === device.ip)
    );
  };

  const deleteGroup = async (groupId) => {
    const groupToDelete = groups.find((g) => g.id === groupId);
    
    try {
      await deviceGroupsAPI.deleteGroup(routerId, groupId);
      
      const updatedGroups = groups.filter((group) => group.id !== groupId);
      setGroups(updatedGroups);

      console.log("Group deleted via backend:", groupToDelete?.name);
    } catch (error) {
      console.error("Failed to delete group:", error);
      alert("Failed to delete group: " + error.message);
    }
  };

  const startRenameGroup = (group) => {
    setEditingGroupId(group.id);
    setEditingGroupName(group.name);
  };

  const saveRenameGroup = async () => {
    if (!editingGroupName.trim()) return;
    
    try {
      await deviceGroupsAPI.updateGroup(routerId, editingGroupId, {
        name: editingGroupName.trim()
      });

      const updatedGroups = groups.map((g) =>
        g.id === editingGroupId ? { ...g, name: editingGroupName.trim() } : g
      );
      setGroups(updatedGroups);
      setEditingGroupId(null);
      setEditingGroupName("");

      console.log("Group renamed via backend");
    } catch (error) {
      console.error("Failed to rename group:", error);
      alert("Failed to rename group: " + error.message);
    }
  };

  const cancelRenameGroup = () => {
    setEditingGroupId(null);
    setEditingGroupName("");
  };

  // Debug function removed - groups now managed via backend

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
      // Build devices list for API from selected groups
      const devicesToApply = [];
      const seenIps = new Set();
      selectedGroups.forEach((groupId) => {
        const group = groups.find((g) => g.id === groupId);
        if (group && Array.isArray(group.devices)) {
          group.devices.forEach((d) => {
            const ip = d?.ip;
            const mac = d?.mac;
            if (ip && !seenIps.has(ip)) {
              seenIps.add(ip);
              devicesToApply.push({ ip, mac });
            }
          });
        }
      });

      if (!routerId) {
        throw new Error("Router ID is missing. Set routerId first in the app.");
      }

      // Determine categories to apply (blocked categories)
      const categoriesToApply = contentCategories
        .filter((cat) => cat.blocked)
        .map((cat) => cat.id);

      // Call backend to set rules for multiple devices
      await aghAPI.setDevicesRules(routerId, devicesToApply, categoriesToApply);

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
      alert(error?.message || "Failed to apply changes. Please try again.");
    } finally {
      setContentLoading(false);
    }
  };

  const handleClearContentRules = async () => {
    if (selectedGroups.length === 0) {
      alert("Please select at least one group to clear.");
      return;
    }
    setContentLoading(true);
    try {
      const devicesToClear = [];
      const seenIps = new Set();
      selectedGroups.forEach((groupId) => {
        const group = groups.find((g) => g.id === groupId);
        if (group && Array.isArray(group.devices)) {
          group.devices.forEach((d) => {
            const ip = d?.ip;
            const mac = d?.mac;
            if (ip && !seenIps.has(ip)) {
              seenIps.add(ip);
              devicesToClear.push({ ip, mac });
            }
          });
        }
      });

      await aghAPI.clearDevicesRules(routerId, devicesToClear);
      setHasContentChanges(false);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 2000);
    } catch (e) {
      console.error('Failed to clear rules:', e);
      alert(e?.message || 'Failed to clear rules');
    } finally {
      setContentLoading(false);
    }
  };

  const openDomainsModal = async (categoryId, name) => {
    if (!routerId) return;
    try {
      const res = await aghAPI.getCategoryDomains(routerId, categoryId);
      const domains = Array.isArray(res?.data?.domains) ? res.data.domains : Array.isArray(res?.domains) ? res.domains : [];
      setDomainsModal({ categoryId, name, domains: [...domains], newDomain: '' });
    } catch (e) {
      alert(e?.message || 'Failed to load domains');
    }
  };

  const saveDomains = async () => {
    if (!domainsModal || !routerId) return;
    try {
      await aghAPI.replaceCategoryDomains(routerId, domainsModal.categoryId, domainsModal.domains);
      setDomainsModal(null);
    } catch (e) {
      alert(e?.message || 'Failed to save domains');
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
      // Build IP list from group devices
      const group = groups.find((g) => g.id === groupId);
      const ips = (group?.devices || []).map((d) => d.ip).filter(Boolean);
      // Apply group limits sending both download and upload (mirror) to satisfy backend validation
      await bandwidthAPI.applyGroupLimits(routerId, ips, { download_mbps: parseFloat(changes.downLimit), upload_mbps: parseFloat(changes.downLimit) });

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
      // Aggregate all IPs across groups
      const ips = [];
      const seen = new Set();
      groups.forEach((g) => (g.devices || []).forEach((d) => {
        if (d?.ip && !seen.has(d.ip)) { seen.add(d.ip); ips.push(d.ip); }
      }));
      await bandwidthAPI.applyGroupLimits(routerId, ips, { download_mbps: parseFloat(bulkValues.downLimit), upload_mbps: parseFloat(bulkValues.downLimit) });

      // Apply to UI state
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

  const handleClearGroupLimits = async (groupId) => {
    try {
      const group = groups.find((g) => g.id === groupId);
      const ips = (group?.devices || []).map((d) => d.ip).filter(Boolean);
      await bandwidthAPI.deleteGroupLimits(routerId, ips);
      // Clear UI value
      setBandwidthGroups((prev) => prev.map((g) => g.id === groupId ? { ...g, downLimit: "" } : g));
      setBandwidthChanges((prev) => {
        const next = { ...prev };
        delete next[groupId];
        return next;
      });
    } catch (e) {
      console.error('Failed to clear group limits:', e);
      alert(e?.message || 'Failed to clear group limits');
    }
  };

  const activateGlobalLimits = async () => {
    if (!globalLimits.dlMbps || !globalLimits.ulMbps) {
      alert('Enter both download and upload Mbps');
      return;
    }
    setGlobalLoading(true);
    try {
      const download_kbytes = Math.round(parseFloat(globalLimits.dlMbps) * 125);
      const upload_kbytes = Math.round(parseFloat(globalLimits.ulMbps) * 125);
      await bandwidthAPI.activateGlobal(routerId, { download_kbytes, upload_kbytes, lan_cidr: globalLimits.lanCidr || undefined });
      alert('Global limits activated');
    } catch (e) {
      console.error('Failed to activate global limits', e);
      alert(e?.message || 'Failed to activate global limits');
    } finally {
      setGlobalLoading(false);
    }
  };

  const deactivateGlobalLimits = async () => {
    setGlobalLoading(true);
    try {
      await bandwidthAPI.deactivateGlobal(routerId);
      alert('Global limits deactivated');
    } catch (e) {
      console.error('Failed to deactivate global limits', e);
      alert(e?.message || 'Failed to deactivate global limits');
    } finally {
      setGlobalLoading(false);
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

  const handleClearAllGroups = async () => {
    try {
      // Aggregate all IPs across groups
      const ips = [];
      const seen = new Set();
      groups.forEach((g) => (g.devices || []).forEach((d) => {
        if (d?.ip && !seen.has(d.ip)) { seen.add(d.ip); ips.push(d.ip); }
      }));

      if (ips.length === 0) {
        alert("No devices found in any groups to clear limits for.");
        return;
      }

      // Clear all group limits
      await bandwidthAPI.deleteGroupLimits(routerId, ips);

      // Clear UI state for all groups
      setBandwidthGroups((prev) =>
        prev.map((group) => ({
          ...group,
          downLimit: "",
        }))
      );

      // Clear any pending changes
      setBandwidthChanges({});
      setErrors({});

      console.log("Cleared bandwidth limits for all groups:", ips.length, "devices");
      alert(`Successfully cleared bandwidth limits for ${ips.length} devices across all groups.`);
    } catch (error) {
      console.error("Failed to clear all group limits:", error);
      alert("Failed to clear all group limits. Please try again.");
    }
  };

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
                              {getDeviceIcon(device.icon)}
                            </span>
                            <span className="text-sm text-gray-700 dark:text-gray-200">
                              {device.hostname} ({device.ip})
                            </span>
                            <button
                              onClick={() => removeDeviceFromGroup(group.id, device.ip)}
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
                    </div>

                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => setShowAddToGroup(group.id)}
                        className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                      >
                        <FaPlus /> Add device
                      </button>
                      <button
                        onClick={() => setConfirmDeleteGroup({ id: group.id, name: group.name })}
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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
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
              <button
                onClick={handleClearAllGroups}
                className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg transition-colors"
              >
                Clear All Groups
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
                      Actions
                    </th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                          Clear
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
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleClearGroupLimits(group.id)}
                            className="px-3 py-1 rounded text-sm bg-gray-200 hover:bg-gray-300"
                          >
                            Clear
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

      {/* Delete Group Confirmation Modal */}
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
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Are you sure you want to delete the group
              {" "}
              <span className="font-semibold">{confirmDeleteGroup.name}</span>?
              This cannot be undone.
            </p>
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
                  <div className="mb-2">
                    <button
                      onClick={() => openDomainsModal(category.id, category.name)}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Manage domains
                    </button>
                  </div>

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

      {/* Global Limits Section */}
      <div className="mb-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">Global Bandwidth Limits</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">Apply limits to all LAN hosts</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Download (Mbps)</label>
              <input className="w-full p-3 border rounded-lg bg-white dark:bg-gray-800" type="number" min="0.1" step="0.1" value={globalLimits.dlMbps}
                onChange={(e)=>setGlobalLimits((p)=>({...p, dlMbps:e.target.value}))}/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Upload (Mbps)</label>
              <input className="w-full p-3 border rounded-lg bg-white dark:bg-gray-800" type="number" min="0.1" step="0.1" value={globalLimits.ulMbps}
                onChange={(e)=>setGlobalLimits((p)=>({...p, ulMbps:e.target.value}))}/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">LAN CIDR (optional)</label>
              <input className="w-full p-3 border rounded-lg bg-white dark:bg-gray-800" placeholder="e.g., 192.168.1.0/24" value={globalLimits.lanCidr}
                onChange={(e)=>setGlobalLimits((p)=>({...p, lanCidr:e.target.value}))}/>
            </div>
            <div className="flex gap-2">
              <button onClick={activateGlobalLimits} disabled={globalLoading}
                className="px-4 py-3 rounded bg-green-600 text-white disabled:opacity-60">Activate</button>
              <button onClick={deactivateGlobalLimits} disabled={globalLoading}
                className="px-4 py-3 rounded bg-gray-300">Deactivate</button>
            </div>
          </div>
        </div>
      </div>

      {/* Success Toast */}
      {showSuccessToast && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <FaCheck />
          Content controls applied successfully!
        </div>
      )}

      {/* Domains modal */}
      {domainsModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 w-full max-w-lg">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold">Manage domains - {domainsModal.name}</h3>
              <button onClick={() => setDomainsModal(null)} className="text-gray-500 hover:text-gray-700">
                <FaTimes />
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto border rounded p-2">
              {(domainsModal.domains || []).map((d, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-100 dark:bg-gray-700 rounded px-2 py-1">
                  <span className="text-sm truncate">{d}</span>
                  <button
                    className="text-red-500 hover:text-red-700"
                    onClick={() => setDomainsModal((prev) => ({
                      ...prev,
                      domains: prev.domains.filter((_, idx) => idx !== i),
                    }))}
                  >
                    <FaTimes />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-3">
              <input
                className="flex-1 border rounded px-2 py-1"
                placeholder="Add domain"
                value={domainsModal.newDomain || ''}
                onChange={(e) => setDomainsModal((prev) => ({ ...prev, newDomain: e.target.value }))}
              />
              <button
                className="px-3 py-1 bg-gray-200 rounded"
                onClick={() => {
                  if (domainsModal.newDomain?.trim()) {
                    setDomainsModal((prev) => ({
                      ...prev,
                      domains: [...prev.domains, prev.newDomain.trim()],
                      newDomain: '',
                    }));
                  }
                }}
              >
                Add
              </button>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button className="px-4 py-2 bg-gray-300 rounded" onClick={() => setDomainsModal(null)}>Cancel</button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={saveDomains}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DevicesPage;
