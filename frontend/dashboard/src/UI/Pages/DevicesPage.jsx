import React, { useState, useEffect } from "react";
// Database Integration Complete:
// - Bandwidth rules are now saved to and loaded from the database
// - Content control rules are now saved to and loaded from the database
// - Rules are applied to both database and actual devices
// - Loading states and error handling for database operations
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
import { aghAPI, bandwidthAPI, deviceGroupsAPI, devicesAPI, bandwidthRulesAPI, contentControlRulesAPI } from "../../constants/api";
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
  const [contentCategories, setContentCategories] = useState([]);
  const [hasContentChanges, setHasContentChanges] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [categoriesError, setCategoriesError] = useState(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [showAddUrlModal, setShowAddUrlModal] = useState(null);
  const [newUrl, setNewUrl] = useState("");
  const [customUrls, setCustomUrls] = useState({});
  const [domainsModal, setDomainsModal] = useState(null); // { categoryId, name, domains: [] }
  const [loadingBlockedState, setLoadingBlockedState] = useState(false);
  
  // New state for per-category group toggles
  const [categoryGroupToggles, setCategoryGroupToggles] = useState({}); // { categoryId: { groupId: boolean } }

  // Database Rules State
  const [bandwidthRules, setBandwidthRules] = useState({}); // { groupId: { download_limit_mbps, upload_limit_mbps, is_active, description } }
  const [contentControlRules, setContentControlRules] = useState({}); // { groupId: { blocked_categories, is_active, description } }
  const [rulesLoading, setRulesLoading] = useState(false);
  const [rulesError, setRulesError] = useState(null);

  // Create Category State
  const [showCreateCategoryModal, setShowCreateCategoryModal] = useState(false);
  const [createCategoryForm, setCreateCategoryForm] = useState({
    name: "",
    domains: [],
    inputMethod: "manual", // "manual" or "file"
    manualDomain: "",
    uploadedFile: null,
    isSubmitting: false
  });

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

  // Helper function to map API category names to UI format with icons and default values
  const mapApiCategoriesToUI = async (categoryNames) => {
    const iconMap = {
      social_media: FaUsers,
      entertainment: FaTv,
      gaming: FaGamepad,
      adult_gambling: EighteenPlusIcon,
      shopping: FaShoppingCart,
      custom: FaCog,
    };

    const nameMap = {
      social_media: "Social Media",
      entertainment: "Video Streaming", 
      gaming: "Gaming",
      adult_gambling: "Adult Content",
      shopping: "Shopping",
      custom: "Custom Sites",
    };

    const descriptionMap = {
      social_media: "Facebook, Instagram, Twitter, TikTok",
      entertainment: "YouTube, Netflix, Twitch, Disney+",
      gaming: "Steam, Epic Games, gaming platforms", 
      adult_gambling: "Adult and explicit content sites",
      shopping: "Amazon, eBay, retail websites",
      custom: "User-defined blocked sites",
    };

    // Get domain counts for each category
    const categoriesWithCounts = [];
    
    for (const categoryId of categoryNames) {
      try {
        // Get domain count for this category
        const domainResponse = await aghAPI.getCategoryDomains(routerId, categoryId);
        const domainCount = domainResponse.data?.count || 0;
        
        categoriesWithCounts.push({
          id: categoryId,
          name: nameMap[categoryId] || categoryId.replace(/__/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          icon: iconMap[categoryId] || FaCog,
          blocked: false, // Default all categories to allowed
          sites: domainCount,
          description: descriptionMap[categoryId] || `${categoryId.replace(/__/g, ' ').replace(/_/g, ' ')} category`,
        });
      } catch (error) {
        console.warn(`Failed to get domain count for category ${categoryId}:`, error);
        // Add category with default count if domain fetch fails
        categoriesWithCounts.push({
          id: categoryId,
          name: nameMap[categoryId] || categoryId.replace(/__/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          icon: iconMap[categoryId] || FaCog,
          blocked: false, // Default all categories to allowed
          sites: 0,
          description: descriptionMap[categoryId] || `${categoryId.replace(/__/g, ' ').replace(/_/g, ' ')} category`,
        });
      }
    }

    return categoriesWithCounts;
  };

  // Load AGH categories dynamically from backend
  useEffect(() => {
    const loadCategories = async () => {
      if (!routerId) return;

      setCategoriesLoading(true);
      setCategoriesError(null);
      
      try {
        console.log("🔄 [DevicesPage] Loading AGH categories from backend...");
        
        // Get category names from backend2 → commands server
        const categoriesResponse = await aghAPI.getCategories(routerId);
        const categoryNames = categoriesResponse.data?.categories || [];
        
        console.log("✅ [DevicesPage] Received categories from API:", categoryNames);
        
        if (categoryNames.length === 0) {
          console.warn("⚠️ [DevicesPage] No categories found, using empty array");
          setContentCategories([]);
          return;
        }

        // Map category names to UI format with domain counts
        console.log("🔄 [DevicesPage] Fetching domain counts for categories...");
        const uiCategories = await mapApiCategoriesToUI(categoryNames);
        
        console.log("✅ [DevicesPage] Categories mapped to UI format:", uiCategories.length, "categories");
        setContentCategories(uiCategories);
        
      } catch (error) {
        console.error("❌ [DevicesPage] Failed to load AGH categories:", error);
        setCategoriesError(`Failed to load categories: ${error.message}`);
        
        // Fallback to empty array on error
        setContentCategories([]);
      } finally {
        setCategoriesLoading(false);
      }
    };

    loadCategories();
  }, [routerId]);

  // Load database rules when groups change
  useEffect(() => {
    const loadDatabaseRules = async () => {
      if (!routerId || groups.length === 0) return;

      setRulesLoading(true);
      setRulesError(null);
      
      try {
        console.log("🔄 [DevicesPage] Loading database rules...");
        
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
        
        console.log("✅ [DevicesPage] Database rules loaded:", {
          bandwidth: Object.keys(bandwidthLookup).length,
          content: Object.keys(contentLookup).length
        });
        
      } catch (error) {
        console.error("❌ [DevicesPage] Failed to load database rules:", error);
        setRulesError(`Failed to load rules: ${error.message}`);
        
        // Fallback to empty objects on error
        setBandwidthRules({});
        setContentControlRules({});
      } finally {
        setRulesLoading(false);
      }
    };

    loadDatabaseRules();
  }, [routerId, groups]);

  // Create Category Helper Functions
  const resetCreateCategoryForm = () => {
    setCreateCategoryForm({
      name: "",
      domains: [],
      inputMethod: "manual",
      manualDomain: "",
      uploadedFile: null,
      isSubmitting: false
    });
  };

  const handleAddManualDomain = () => {
    const domain = createCategoryForm.manualDomain.trim();
    if (domain && !createCategoryForm.domains.includes(domain)) {
      setCreateCategoryForm(prev => ({
        ...prev,
        domains: [...prev.domains, domain],
        manualDomain: ""
      }));
    }
  };

  const handleRemoveDomain = (index) => {
    setCreateCategoryForm(prev => ({
      ...prev,
      domains: prev.domains.filter((_, i) => i !== index)
    }));
  };

  const handleFileUpload = (file) => {
    if (file && file.type === "text/plain") {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        const domains = content
          .split('\n')
          .map(line => line.trim())
          .filter(line => line && !line.startsWith('#')) // Filter out empty lines and comments
          .filter((domain, index, arr) => arr.indexOf(domain) === index); // Remove duplicates
        
        setCreateCategoryForm(prev => ({
          ...prev,
          domains: domains,
          uploadedFile: file
        }));
      };
      reader.readAsText(file);
    } else {
      alert("Please upload a .txt file");
    }
  };

  const handleCreateCategory = async () => {
    if (!createCategoryForm.name.trim()) {
      alert("Please enter a category name");
      return;
    }

    if (createCategoryForm.domains.length === 0) {
      alert("Please add at least one domain");
      return;
    }

    // Convert user input to valid category format
    const sanitizedCategoryName = createCategoryForm.name.trim()
      .toLowerCase()
      .replace(/\s+/g, '__') // Replace spaces with double underscores
      .replace(/[^a-z0-9._-]/g, ''); // Remove any invalid characters

    setCreateCategoryForm(prev => ({ ...prev, isSubmitting: true }));

    try {
      console.log("🔄 [DevicesPage] Creating new category:", createCategoryForm.name);
      console.log("🔧 [DevicesPage] Sanitized name:", sanitizedCategoryName);
      console.log("📋 [DevicesPage] Domains:", createCategoryForm.domains);

      // Call the API to create the category (use sanitized name)
      const response = await aghAPI.createCategory(routerId, sanitizedCategoryName, createCategoryForm.domains);
      
      console.log("✅ [DevicesPage] Category created successfully:", response);

      // Close modal and reset form
      setShowCreateCategoryModal(false);
      resetCreateCategoryForm();

      // Add the new category to existing list instead of reloading all
      console.log("🔄 [DevicesPage] Adding new category to list...");
      
      try {
        // Get domain count for the new category
        const domainResponse = await aghAPI.getCategoryDomains(routerId, sanitizedCategoryName);
        const domainCount = domainResponse.data?.count || createCategoryForm.domains.length;
        
        // Create the new category UI object
        const newCategory = {
          id: sanitizedCategoryName,
          name: createCategoryForm.name.trim(), // Use original user input for display
          icon: FaCog, // Default icon for custom categories
          blocked: false,
          sites: domainCount,
          description: `${createCategoryForm.name.trim()} category`,
        };

        // Add to existing categories
        setContentCategories(prev => [...prev, newCategory]);
        console.log("✅ [DevicesPage] New category added to list:", newCategory.name);
        
      } catch (error) {
        console.warn("⚠️ [DevicesPage] Failed to get domain count for new category, using fallback");
        // Fallback: add with domain count from form
        const newCategory = {
          id: sanitizedCategoryName,
          name: createCategoryForm.name.trim(),
          icon: FaCog,
          blocked: false,
          sites: createCategoryForm.domains.length,
          description: `${createCategoryForm.name.trim()} category`,
        };
        setContentCategories(prev => [...prev, newCategory]);
      }

      // Show success message
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);

    } catch (error) {
      console.error("❌ [DevicesPage] Failed to create category:", error);
      alert(`Failed to create category: ${error.message}`);
    } finally {
      setCreateCategoryForm(prev => ({ ...prev, isSubmitting: false }));
    }
  };





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
  const handleContentToggle = (categoryId, groupId) => {
    setCategoryGroupToggles((prev) => ({
      ...prev,
      [categoryId]: {
        ...(prev[categoryId] || {}),
        [groupId]: !(prev[categoryId]?.[groupId] || false)
      }
    }));
  };

  // Initialize category group toggles when groups or categories change
  useEffect(() => {
    if (groups.length > 0 && contentCategories.length > 0) {
      const initialToggles = {};
      contentCategories.forEach(category => {
        initialToggles[category.id] = {};
        groups.forEach(group => {
          // Initialize all toggles to false initially
          // The actual blocked state will be loaded from backend if available
          initialToggles[category.id][group.id] = false;
        });
      });
      setCategoryGroupToggles(initialToggles);
      
      // Load current blocked state from backend
      loadCurrentBlockedState();
    }
  }, [groups, contentCategories]);

  // Get summary of pending changes
  const getChangesSummary = () => {
    const summary = {};
    
    Object.keys(categoryGroupToggles).forEach(categoryId => {
      const category = contentCategories.find(c => c.id === categoryId);
      if (category) {
        const blockedGroups = [];
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          if (categoryGroupToggles[categoryId][groupId]) {
            const group = groups.find(g => g.id === groupId);
            if (group) {
              blockedGroups.push(group.name);
            }
          }
        });
        if (blockedGroups.length > 0) {
          summary[category.name] = blockedGroups;
        }
      }
    });
    
    return summary;
  };

  // Check if there are any pending changes
  const hasPendingChanges = () => {
    return Object.keys(categoryGroupToggles).some(categoryId => 
      Object.keys(categoryGroupToggles[categoryId]).some(groupId => 
        categoryGroupToggles[categoryId][groupId]
      )
    );
  };

  // Update hasContentChanges when categoryGroupToggles change
  useEffect(() => {
    setHasContentChanges(hasPendingChanges());
  }, [categoryGroupToggles]);

  // Reset all toggles to false
  const resetAllToggles = () => {
    const resetToggles = {};
    contentCategories.forEach(category => {
      resetToggles[category.id] = {};
      groups.forEach(group => {
        resetToggles[category.id][group.id] = false;
      });
    });
    setCategoryGroupToggles(resetToggles);
  };

  // Load current blocked state from database and backend
  const loadCurrentBlockedState = async () => {
    if (!routerId || groups.length === 0 || contentCategories.length === 0) return;
    
    setLoadingBlockedState(true);
    try {
      // First, try to load from database rules
      const updatedToggles = { ...categoryGroupToggles };
      
      // Initialize toggles from database rules
      for (const group of groups) {
        const groupRules = contentControlRules[group.id];
        if (groupRules && groupRules.blocked_categories) {
          contentCategories.forEach(category => {
            if (updatedToggles[category.id]) {
              updatedToggles[category.id][group.id] = groupRules.blocked_categories.includes(category.id);
            }
          });
        }
      }
      
      // Fallback: check AGH API for any groups without database rules
      for (const group of groups) {
        if (!contentControlRules[group.id] && group.devices && group.devices.length > 0) {
          try {
            // Get current rules for the first device in the group
            const device = group.devices[0];
            if (device.ip) {
              const rulesResponse = await aghAPI.getDeviceRules(routerId, { ip: device.ip });
              const blockedCategories = rulesResponse.data?.categories || [];
              
              // Update toggles based on current blocked state
              contentCategories.forEach(category => {
                if (updatedToggles[category.id]) {
                  updatedToggles[category.id][group.id] = blockedCategories.includes(category.id);
                }
              });
            }
          } catch (error) {
            console.warn(`Failed to load AGH rules for group ${group.name}:`, error);
            // Continue with other groups even if one fails
          }
        }
      }
      
      setCategoryGroupToggles(updatedToggles);
    } catch (error) {
      console.warn('Failed to load current blocked state:', error);
    } finally {
      setLoadingBlockedState(false);
    }
  };



  const handleApplyContentChanges = async () => {
    // Check if any changes exist
    if (!hasPendingChanges()) {
      return;
    }

    setContentLoading(true);
    try {
      // Build a map of groups to their blocked categories
      const groupCategoryMap = {};
      
      Object.keys(categoryGroupToggles).forEach(categoryId => {
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          if (categoryGroupToggles[categoryId][groupId]) {
            if (!groupCategoryMap[groupId]) {
              groupCategoryMap[groupId] = [];
            }
            groupCategoryMap[groupId].push(categoryId);
          }
        });
      });

      // Save rules to database first
      for (const [groupId, categoryIds] of Object.entries(groupCategoryMap)) {
        if (categoryIds.length > 0) {
          try {
            await contentControlRulesAPI.setGroupRules(routerId, groupId, {
              blocked_categories: categoryIds,
              description: `Content control rules for ${groups.find(g => g.id === groupId)?.name || 'Unknown Group'}`,
              is_active: true
            });
            console.log(`✅ Database rules saved for group ${groupId}:`, categoryIds);
          } catch (dbError) {
            console.error(`❌ Failed to save database rules for group ${groupId}:`, dbError);
            // Continue with other groups even if one fails
          }
        }
      }

      // Apply rules to actual devices via AGH API
      for (const [groupId, categoryIds] of Object.entries(groupCategoryMap)) {
        if (categoryIds.length > 0) {
          const group = groups.find(g => g.id === groupId);
          if (group && Array.isArray(group.devices)) {
            const devicesToApply = group.devices.map(d => ({ ip: d.ip, mac: d.mac })).filter(d => d.ip);
            if (devicesToApply.length > 0) {
              await aghAPI.setDevicesRules(routerId, devicesToApply, categoryIds);
              console.log(`✅ AGH rules applied for group ${groupId}:`, devicesToApply.length, 'devices');
            }
          }
        }
      }

      // Update local state
      setContentControlRules(prev => {
        const updated = { ...prev };
        Object.entries(groupCategoryMap).forEach(([groupId, categoryIds]) => {
          updated[groupId] = {
            blocked_categories: categoryIds,
            is_active: true,
            description: `Content control rules for ${groups.find(g => g.id === groupId)?.name || 'Unknown Group'}`
          };
        });
        return updated;
      });

      setHasContentChanges(false);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);

      console.log("Content controls applied successfully to database and devices");
    } catch (error) {
      console.error("Failed to apply content changes:", error);
      alert(error?.message || "Failed to apply changes. Please try again.");
    } finally {
      setContentLoading(false);
    }
  };

  const handleClearContentRules = async () => {
    if (!hasPendingChanges()) {
      return;
    }
    
    setContentLoading(true);
    try {
      // Clear rules for all groups that have any categories blocked
      const groupsToClear = new Set();
      
      Object.keys(categoryGroupToggles).forEach(categoryId => {
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          if (categoryGroupToggles[categoryId][groupId]) {
            groupsToClear.add(groupId);
          }
        });
      });

      // Clear database rules first
      for (const groupId of groupsToClear) {
        try {
          await contentControlRulesAPI.deleteGroupRules(routerId, groupId);
          console.log(`✅ Database rules cleared for group ${groupId}`);
        } catch (dbError) {
          console.error(`❌ Failed to clear database rules for group ${groupId}:`, dbError);
          // Continue with other groups even if one fails
        }
      }

      // Clear AGH rules from actual devices
      for (const groupId of groupsToClear) {
        const group = groups.find(g => g.id === groupId);
        if (group && Array.isArray(group.devices)) {
          const devicesToClear = group.devices.map(d => ({ ip: d.ip, mac: d.mac })).filter(d => d.ip);
          if (devicesToClear.length > 0) {
            await aghAPI.clearDevicesRules(routerId, devicesToClear);
            console.log(`✅ AGH rules cleared for group ${groupId}:`, devicesToClear.length, 'devices');
          }
        }
      }

      // Update local state
      setContentControlRules(prev => {
        const updated = { ...prev };
        groupsToClear.forEach(groupId => {
          delete updated[groupId];
        });
        return updated;
      });

      // Reset all toggles to false
      resetAllToggles();
      setHasContentChanges(false);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 2000);
      
      console.log("Content control rules cleared from database and devices");
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
      
      // Update the category count in the UI
      const newDomainCount = domainsModal.domains.length;
      setContentCategories(prev => prev.map(category => 
        category.id === domainsModal.categoryId 
          ? { ...category, sites: newDomainCount }
          : category
      ));
      
      console.log(`✅ [DevicesPage] Updated domain count for ${domainsModal.categoryId}: ${newDomainCount} domains`);
      
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

  const handleDeleteCategory = async (categoryId) => {
    // Check if it's a default category
    const defaultCategories = ["social_media", "entertainment", "gaming", "adult_gambling"];
    if (defaultCategories.includes(categoryId)) {
      alert("Cannot delete default categories. Only custom categories can be deleted.");
      return;
    }

    // Confirm deletion
    if (!confirm(`Are you sure you want to delete the category "${categoryId}"? This action cannot be undone.`)) {
      return;
    }

    try {
      console.log("🔄 [DevicesPage] Deleting category:", categoryId);
      
      // Call the API to delete the category
      await aghAPI.deleteCategory(routerId, categoryId);
      
      console.log("✅ [DevicesPage] Category deleted successfully:", categoryId);
      
      // Remove the category from the local state
      setContentCategories(prev => prev.filter(cat => cat.id !== categoryId));
      
      // Show success message
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);
      
    } catch (error) {
      console.error("❌ [DevicesPage] Failed to delete category:", error);
      alert(`Failed to delete category: ${error.message}`);
    }
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
      // Save to database first
      const downloadLimit = changes.downLimit !== undefined && changes.downLimit !== "" 
        ? parseFloat(changes.downLimit) 
        : null;
      
      await bandwidthRulesAPI.setGroupRules(routerId, groupId, {
        download_limit_mbps: downloadLimit,
        upload_limit_mbps: downloadLimit, // Mirror download limit for now
        description: `Bandwidth rules for ${groups.find(g => g.id === groupId)?.name || 'Unknown Group'}`,
        is_active: true
      });

      // Apply to actual devices via legacy API
      const group = groups.find((g) => g.id === groupId);
      const ips = (group?.devices || []).map((d) => d.ip).filter(Boolean);
      if (ips.length > 0) {
        await bandwidthAPI.applyGroupLimits(routerId, ips, { 
          download_mbps: downloadLimit || 0, 
          upload_mbps: downloadLimit || 0 
        });
      }

      // Update local state
      setBandwidthRules(prev => ({
        ...prev,
        [groupId]: {
          download_limit_mbps: downloadLimit,
          upload_limit_mbps: downloadLimit,
          is_active: true,
          description: `Bandwidth rules for ${groups.find(g => g.id === groupId)?.name || 'Unknown Group'}`
        }
      }));

      // Update bandwidth groups with new values
      setBandwidthGroups((prev) =>
        prev.map((group) =>
          group.id === groupId
            ? {
                ...group,
                downLimit: downloadLimit || "",
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

      console.log("Bandwidth limits applied to database and devices for group:", groupId, changes);
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
      const downloadLimit = parseFloat(bulkValues.downLimit);
      
      // Save to database for all groups
      for (const group of groups) {
        try {
          await bandwidthRulesAPI.setGroupRules(routerId, group.id, {
            download_limit_mbps: downloadLimit,
            upload_limit_mbps: downloadLimit, // Mirror download limit for now
            description: `Bulk applied bandwidth rules for ${group.name}`,
            is_active: true
          });
          console.log(`✅ Database rules saved for group ${group.id}:`, downloadLimit);
        } catch (dbError) {
          console.error(`❌ Failed to save database rules for group ${group.id}:`, dbError);
          // Continue with other groups even if one fails
        }
      }

      // Aggregate all IPs across groups and apply to actual devices
      const ips = [];
      const seen = new Set();
      groups.forEach((g) => (g.devices || []).forEach((d) => {
        if (d?.ip && !seen.has(d.ip)) { seen.add(d.ip); ips.push(d.ip); }
      }));
      
      if (ips.length > 0) {
        await bandwidthAPI.applyGroupLimits(routerId, ips, { 
          download_mbps: downloadLimit, 
          upload_mbps: downloadLimit 
        });
      }

      // Update local state
      setBandwidthRules(prev => {
        const updated = { ...prev };
        groups.forEach(group => {
          updated[group.id] = {
            download_limit_mbps: downloadLimit,
            upload_limit_mbps: downloadLimit,
            is_active: true,
            description: `Bulk applied bandwidth rules for ${group.name}`
          };
        });
        return updated;
      });

      // Apply to UI state
      setBandwidthGroups((prev) =>
        prev.map((group) => ({
          ...group,
          downLimit: downloadLimit,
        }))
      );

      setBulkValues({ downLimit: "" });
      setErrors({});

      console.log("Bulk bandwidth limits applied to database and devices:", downloadLimit);
    } catch (error) {
      console.error("Failed to apply bulk changes:", error);
      alert("Failed to apply changes. Please try again.");
    }
  };

  const handleClearGroupLimits = async (groupId) => {
    try {
      // Clear from database first
      await bandwidthRulesAPI.deleteGroupRules(routerId, groupId);
      
      // Clear from actual devices
      const group = groups.find((g) => g.id === groupId);
      const ips = (group?.devices || []).map((d) => d.ip).filter(Boolean);
      if (ips.length > 0) {
        await bandwidthAPI.deleteGroupLimits(routerId, ips);
      }
      
      // Update local state
      setBandwidthRules(prev => {
        const updated = { ...prev };
        delete updated[groupId];
        return updated;
      });
      
      // Clear UI value
      setBandwidthGroups((prev) => prev.map((g) => g.id === groupId ? { ...g, downLimit: "" } : g));
      setBandwidthChanges((prev) => {
        const next = { ...prev };
        delete next[groupId];
        return next;
      });
      
      console.log("Bandwidth limits cleared from database and devices for group:", groupId);
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

  // Initialize bandwidth groups from device groups and database rules
  useEffect(() => {
    const bandwidthData = groups.map((group) => {
      const dbRules = bandwidthRules[group.id];
      return {
        id: group.id,
        name: group.name,
        deviceCount: group.devices.length,
        downLimit: dbRules?.download_limit_mbps || "", // Use database rules if available
        enabled: dbRules?.is_active || false, // Use database rules if available
      };
    });
    setBandwidthGroups(bandwidthData);
  }, [groups, bandwidthRules]);

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

      // Clear all group limits from database
      for (const group of groups) {
        try {
          await bandwidthRulesAPI.deleteGroupRules(routerId, group.id);
          console.log(`✅ Database rules cleared for group ${group.id}`);
        } catch (dbError) {
          console.error(`❌ Failed to clear database rules for group ${group.id}:`, dbError);
          // Continue with other groups even if one fails
        }
      }

      // Clear all group limits from actual devices
      await bandwidthAPI.deleteGroupLimits(routerId, ips);

      // Clear local state
      setBandwidthRules({});
      setBandwidthGroups((prev) =>
        prev.map((group) => ({
          ...group,
          downLimit: "",
        }))
      );

      // Clear any pending changes
      setBandwidthChanges({});
      setErrors({});

      console.log("Cleared bandwidth limits from database and devices for all groups:", ips.length, "devices");
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

          {/* Database Rules Status */}
          {!rulesLoading && !rulesError && Object.keys(bandwidthRules).length > 0 && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  ✅ Database Rules Active
                </span>
                <span className="text-xs text-green-600 dark:text-green-400">
                  {Object.keys(bandwidthRules).length} groups have bandwidth rules saved
                </span>
              </div>
            </div>
          )}

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
          {rulesLoading ? (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                Loading bandwidth rules...
              </p>
            </div>
          ) : bandwidthGroups.length > 0 ? (
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
                Block website categories for device groups
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowCreateCategoryModal(true)}
                className="bg-green-500 hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                <FaPlus className="text-sm" />
                Create Category
              </button>
              <button
                onClick={handleClearContentRules}
                disabled={contentLoading}
                className="bg-gray-500 hover:bg-gray-600 dark:bg-gray-600 dark:hover:bg-gray-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                <FaTimes className="text-sm" />
                Clear All Rules
              </button>
              {hasContentChanges && (
                <button
                  onClick={handleApplyContentChanges}
                  disabled={contentLoading}
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
                      <span className="ml-1 px-2 py-1 bg-blue-600 rounded-full text-xs">
                        {Object.keys(categoryGroupToggles).reduce((total, categoryId) => 
                          total + Object.values(categoryGroupToggles[categoryId] || {}).filter(Boolean).length, 0
                        )}
                      </span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Database Rules Status */}
          {!rulesLoading && !rulesError && Object.keys(contentControlRules).length > 0 && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  ✅ Database Rules Active
                </span>
                <span className="text-xs text-green-600 dark:text-green-400">
                  {Object.keys(contentControlRules).length} groups have content control rules saved
                </span>
              </div>
            </div>
          )}

          {/* Summary of Changes */}
          {hasContentChanges && (
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <FaCog className="text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Changes Pending
                </span>
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                {Object.entries(getChangesSummary()).map(([categoryName, groupNames]) => (
                  <div key={categoryName} className="flex items-start gap-2">
                    <span className="font-medium">• {categoryName}:</span>
                    <span>Block for {groupNames.join(', ')}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                Click "Apply Changes" to save these rules.
              </p>
            </div>
          )}

          {/* Category Cards Grid */}
          {categoriesError && (
            <div className="mb-4 p-4 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700 rounded-lg">
              <p className="text-red-700 dark:text-red-300 text-sm">
                {categoriesError}
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-2 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200 text-sm underline"
              >
                Retry
              </button>
            </div>
          )}
          
          {rulesError && (
            <div className="mb-4 p-4 bg-orange-100 dark:bg-orange-900 border border-orange-300 dark:border-orange-700 rounded-lg">
              <p className="text-orange-700 dark:text-orange-300 text-sm">
                Database Rules Error: {rulesError}
              </p>
              <p className="text-orange-600 dark:text-orange-400 text-xs mt-1">
                Some features may not work properly. Rules will be saved locally only.
              </p>
            </div>
          )}
          
          {!rulesLoading && !rulesError && Object.keys(bandwidthRules).length > 0 && (
            <div className="mb-4 p-4 bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-700 rounded-lg">
              <p className="text-green-700 dark:text-green-300 text-sm">
                ✅ Database rules loaded successfully
              </p>
              <p className="text-green-600 dark:text-green-400 text-xs mt-1">
                {Object.keys(bandwidthRules).length} bandwidth rules and {Object.keys(contentControlRules).length} content control rules loaded from database.
              </p>
            </div>
          )}
          
          {categoriesLoading || rulesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Loading skeleton cards */}
              {[...Array(6)].map((_, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border animate-pulse"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded"></div>
                      <div>
                        <div className="w-24 h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                        <div className="w-16 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                      </div>
                    </div>
                  </div>
                  <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="w-20 h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {contentCategories.length === 0 ? (
                <div className="col-span-full text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">
                    No content categories available. Categories will be created automatically when you start a session.
                  </p>
                </div>
              ) : (
                contentCategories.map((category) => {
              const IconComponent = category.icon;
              const categoryUrls = customUrls[category.id] || [];
              return (
                <div
                  key={category.id}
                  className="border rounded-lg p-4 transition-all hover:shadow-md border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-700"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-800 dark:text-blue-300">
                        <IconComponent className="text-lg" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-800 dark:text-white">
                          {category.name}
                        </h3>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100">
                          {category.sites + categoryUrls.length} sites
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Delete button - only show for custom categories */}
                      {!["social_media", "entertainment", "gaming", "adult_gambling"].includes(category.id) && (
                        <button
                          onClick={() => handleDeleteCategory(category.id)}
                          className="p-1 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                          title="Delete category"
                        >
                          <FaTrash className="text-sm" />
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
                    {category.description}
                  </p>
                  
                  {/* Group Toggles Section */}
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Block for Groups:
                    </h4>
                    {loadingBlockedState ? (
                      <div className="text-center py-2">
                        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Loading current rules...</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {groups.map((group) => (
                          <div key={group.id} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <FaUsers className="text-xs text-gray-500" />
                              <span className="text-sm text-gray-600 dark:text-gray-300">
                                {group.name} ({group.devices.length})
                              </span>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={categoryGroupToggles[category.id]?.[group.id] || false}
                                onChange={() => handleContentToggle(category.id, group.id)}
                                className="sr-only peer"
                              />
                              <div className="w-9 h-5 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 dark:after:border-gray-500 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-red-600 dark:peer-checked:bg-red-500"></div>
                            </label>
                          </div>
                        ))}
                        {groups.length === 0 && (
                          <div className="text-center py-4">
                            <FaUsers className="text-gray-400 dark:text-gray-500 mx-auto mb-2 text-lg" />
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                              No groups available
                            </p>
                            <button
                              onClick={() => setShowCreateGroup(true)}
                              className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline"
                            >
                              Create your first group
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="mb-2">
                    <button
                      onClick={() => openDomainsModal(category.id, category.name)}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline"
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
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                        {Object.values(categoryGroupToggles[category.id] || {}).some(Boolean) ? "BLOCKED" : "ALLOWED"}
                      </span>
                      {Object.values(categoryGroupToggles[category.id] || {}).some(Boolean) && (
                        <FaEyeSlash className="text-red-500 text-xs" />
                      )}
                      {Object.values(categoryGroupToggles[category.id] || {}).some(Boolean) && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ({Object.values(categoryGroupToggles[category.id] || {}).filter(Boolean).length} group{Object.values(categoryGroupToggles[category.id] || {}).filter(Boolean).length !== 1 ? 's' : ''})
                        </span>
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
                })
              )}
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
              <input className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400" type="number" min="0.1" step="0.1" value={globalLimits.dlMbps}
                onChange={(e)=>setGlobalLimits((p)=>({...p, dlMbps:e.target.value}))}/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Upload (Mbps)</label>
              <input className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400" type="number" min="0.1" step="0.1" value={globalLimits.ulMbps}
                onChange={(e)=>setGlobalLimits((p)=>({...p, ulMbps:e.target.value}))}/>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">LAN CIDR (optional)</label>
              <input className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400" placeholder="e.g., 192.168.1.0/24" value={globalLimits.lanCidr}
                onChange={(e)=>setGlobalLimits((p)=>({...p, lanCidr:e.target.value}))}/>
            </div>
            <div className="flex gap-2">
              <button onClick={activateGlobalLimits} disabled={globalLoading}
                className="px-4 py-3 rounded bg-green-600 dark:bg-green-500 text-white hover:bg-green-700 dark:hover:bg-green-400 disabled:opacity-60 transition-colors">Activate</button>
              <button onClick={deactivateGlobalLimits} disabled={globalLoading}
                className="px-4 py-3 rounded bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-400 dark:hover:bg-gray-500 disabled:opacity-60 transition-colors">Deactivate</button>
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
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Manage domains - {domainsModal.name}</h3>
              <button onClick={() => setDomainsModal(null)} className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                <FaTimes />
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded p-2">
              {(domainsModal.domains || []).map((d, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-100 dark:bg-gray-700 rounded px-2 py-1">
                  <span className="text-sm text-gray-800 dark:text-gray-200 truncate">{d}</span>
                  <button
                    className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
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
                className="flex-1 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400"
                placeholder="Add domain"
                value={domainsModal.newDomain || ''}
                onChange={(e) => setDomainsModal((prev) => ({ ...prev, newDomain: e.target.value }))}
              />
              <button
                className="px-3 py-1 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500 rounded transition-colors"
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
              <button className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-400 dark:hover:bg-gray-500 rounded transition-colors" onClick={() => setDomainsModal(null)}>Cancel</button>
              <button className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-400 rounded transition-colors" onClick={saveDomains}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Create Category Modal */}
      {showCreateCategoryModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Create New Category</h3>
              <button 
                onClick={() => {
                  setShowCreateCategoryModal(false);
                  resetCreateCategoryForm();
                }}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>

            {/* Category Name */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category Name *
              </label>
              <input
                type="text"
                value={createCategoryForm.name}
                onChange={(e) => setCreateCategoryForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Custom News, My Category, Test Sites"
                className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {createCategoryForm.name ? (
                  <>
                    Will be saved as: <span className="font-mono text-blue-600 dark:text-blue-400">
                      {createCategoryForm.name.trim().toLowerCase().replace(/\s+/g, '__').replace(/[^a-z0-9._-]/g, '')}
                    </span>
                  </>
                ) : (
                  'Enter any name - spaces and special characters will be automatically converted'
                )}
              </p>
            </div>

            {/* Input Method Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                How would you like to add domains?
              </label>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="inputMethod"
                    value="manual"
                    checked={createCategoryForm.inputMethod === "manual"}
                    onChange={(e) => setCreateCategoryForm(prev => ({ ...prev, inputMethod: e.target.value }))}
                    className="mr-2"
                  />
                  <span className="text-gray-700 dark:text-gray-300">Manual Entry</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="inputMethod"
                    value="file"
                    checked={createCategoryForm.inputMethod === "file"}
                    onChange={(e) => setCreateCategoryForm(prev => ({ ...prev, inputMethod: e.target.value }))}
                    className="mr-2"
                  />
                  <span className="text-gray-700 dark:text-gray-300">Upload File</span>
                </label>
              </div>
            </div>

            {/* Manual Domain Entry */}
            {createCategoryForm.inputMethod === "manual" && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Add Domains
                </label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={createCategoryForm.manualDomain}
                    onChange={(e) => setCreateCategoryForm(prev => ({ ...prev, manualDomain: e.target.value }))}
                    placeholder="example.com"
                    onKeyPress={(e) => e.key === 'Enter' && handleAddManualDomain()}
                    className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400"
                  />
                  <button
                    onClick={handleAddManualDomain}
                    className="px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white hover:bg-blue-600 dark:hover:bg-blue-500 rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}

            {/* File Upload */}
            {createCategoryForm.inputMethod === "file" && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Upload Domains File
                </label>
                <div 
                  className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                      handleFileUpload(files[0]);
                    }
                  }}
                  onClick={() => {
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = '.txt';
                    input.onchange = (e) => {
                      const file = e.target.files[0];
                      if (file) handleFileUpload(file);
                    };
                    input.click();
                  }}
                >
                  {createCategoryForm.uploadedFile ? (
                    <div className="text-green-600 dark:text-green-400">
                      <FaCheck className="mx-auto mb-2 text-2xl" />
                      <p>File uploaded: {createCategoryForm.uploadedFile.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {createCategoryForm.domains.length} domains found
                      </p>
                    </div>
                  ) : (
                    <div className="text-gray-500 dark:text-gray-400">
                      <FaDownload className="mx-auto mb-2 text-2xl" />
                      <p>Drag & drop a .txt file here, or click to browse</p>
                      <p className="text-sm">One domain per line</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Domain List */}
            {createCategoryForm.domains.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Domains ({createCategoryForm.domains.length})
                </label>
                <div className="max-h-40 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg p-2 space-y-1">
                  {createCategoryForm.domains.map((domain, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-100 dark:bg-gray-700 rounded px-2 py-1">
                      <span className="text-sm text-gray-800 dark:text-gray-200 truncate">{domain}</span>
                      <button
                        onClick={() => handleRemoveDomain(index)}
                        className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 ml-2"
                      >
                        <FaTimes className="text-xs" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateCategoryModal(false);
                  resetCreateCategoryForm();
                }}
                className="px-6 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 hover:bg-gray-400 dark:hover:bg-gray-500 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCategory}
                disabled={createCategoryForm.isSubmitting || !createCategoryForm.name.trim() || createCategoryForm.domains.length === 0}
                className="px-6 py-2 bg-green-600 dark:bg-green-500 text-white hover:bg-green-700 dark:hover:bg-green-400 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
              >
                {createCategoryForm.isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <FaCheck className="text-sm" />
                    Create Category
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DevicesPage;
