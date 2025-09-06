import React, { useState, useEffect, useRef } from "react";
// Database Integration Complete:
// - Bandwidth rules are now saved to and loaded from the database
// - Content control rules are now saved to and loaded from the database
// - Rules are applied to both database and actual devices
// - Loading states and error handling for database operations
// 
// SIMPLE SEQUENTIAL LOADING IMPLEMENTATION:
// - Only domain requests are queued to prevent SSH server overload
// - Basic functionality restored with minimal changes
// - Focus on fixing the concurrent request issue without breaking the page
import {
  FaPlus,
  FaTimes,
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
  FaTrash,
  FaUndo,
  FaRegQuestionCircle,
  FaTv,
  FaToggleOn,
  FaToggleOff,
} from "react-icons/fa";

import { aghAPI, bandwidthAPI, deviceGroupsAPI, bandwidthRulesAPI, contentControlRulesAPI, scheduledTasksAPI } from "../../constants/api";
import { useAuth } from "../../context/AuthContext.jsx";
import { groupTasksIntoRules } from "../../utils/taskUtils";

// Icon mapping
const getDeviceIcon = (iconName) => {
  // For now, just return a default icon since we're not using device icons in control page
  return <FaRegQuestionCircle className="text-lg" />;
};

// Custom 24-hour time input component
const CustomTimeInput = ({ value, onChange, placeholder = "00:00" }) => {
  const [inputValue, setInputValue] = useState(value || "");
  const [isValid, setIsValid] = useState(true);
  const inputRef = useRef(null);

  useEffect(() => {
    setInputValue(value || "");
  }, [value]);

  const validateAndFormatTime = (timeStr) => {
    // Remove any non-digit characters except colon
    const cleaned = timeStr.replace(/[^\d:]/g, '');
    
    // Handle different input patterns
    if (cleaned.length <= 2) {
      // Just hours: "22" -> "22:"
      return cleaned;
    } else if (cleaned.length === 3) {
      // "223" -> "22:3"
      return cleaned.substring(0, 2) + ':' + cleaned.substring(2);
    } else if (cleaned.length === 4 && !cleaned.includes(':')) {
      // "2230" -> "22:30"
      return cleaned.substring(0, 2) + ':' + cleaned.substring(2);
    } else {
      // Already has colon or longer
      const parts = cleaned.split(':');
      if (parts.length >= 2) {
        const hours = parts[0].substring(0, 2);
        const minutes = parts[1].substring(0, 2);
        return hours + (minutes ? ':' + minutes : ':');
      }
      return cleaned;
    }
  };

  const isValidTime = (timeStr) => {
    const timeRegex = /^([01]?[0-9]|2[0-3]):([0-5][0-9])$/;
    return timeRegex.test(timeStr);
  };

  const handleInputChange = (e) => {
    const rawValue = e.target.value;
    const formatted = validateAndFormatTime(rawValue);
    setInputValue(formatted);

    // Check if it's a complete valid time
    if (isValidTime(formatted)) {
      setIsValid(true);
      onChange(formatted);
    } else if (formatted.length < 5) {
      // Still typing, don't mark as invalid yet
      setIsValid(true);
    } else {
      setIsValid(false);
    }
  };

  const handleBlur = () => {
    if (inputValue && !isValidTime(inputValue)) {
      // Try to auto-complete incomplete times
      const parts = inputValue.split(':');
      if (parts.length === 2) {
        const hours = parseInt(parts[0]) || 0;
        const minutes = parseInt(parts[1]) || 0;
        
        if (hours <= 23 && minutes <= 59) {
          const corrected = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
          setInputValue(corrected);
          setIsValid(true);
          onChange(corrected);
          return;
        }
      }
      setIsValid(false);
    }
  };

  const handleFocus = (e) => {
    e.target.select();
  };

  const handleClick = (e) => {
    e.target.select();
  };

  return (
    <input
      ref={inputRef}
      type="text"
      value={inputValue}
      onChange={handleInputChange}
      onBlur={handleBlur}
      onFocus={handleFocus}
      onClick={handleClick}
      placeholder={placeholder}
      maxLength={5}
      className={`w-full p-3 border rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-center ${
        isValid 
          ? 'border-gray-300 dark:border-gray-600' 
          : 'border-red-500 dark:border-red-400'
      }`}
      style={{ letterSpacing: '0.1em' }}
    />
  );
};

// Custom 18+ Icon Component
const EighteenPlusIcon = ({ className }) => (
  <div className={`flex items-center justify-center ${className}`}>
    <span className="font-bold text-sm">18+</span>
  </div>
);

const ControlPage = () => {
  const { routerId } = useAuth();
  const [groups, setGroups] = useState([]);
  
  // Debug logging
  console.log("🔍 [ControlPage] Component rendered with routerId:", routerId);

  // Content Controls State
  const [contentCategories, setContentCategories] = useState(() => {
    // Try to load categories from localStorage on initialization
    try {
      const stored = localStorage.getItem('netpilot_categories');
      const parsed = stored ? JSON.parse(stored) : [];
      console.log('🔍 [ControlPage] Loaded categories from localStorage on init:', parsed.length, 'categories', parsed);
      return parsed;
    } catch (error) {
      console.warn('Failed to load categories from localStorage:', error);
      return [];
    }
  });
  const [hasContentChanges, setHasContentChanges] = useState(false);
  const [contentApplyLoading, setContentApplyLoading] = useState(false);
  const [contentClearLoading, setContentClearLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [categoriesError, setCategoriesError] = useState(null);
  const [showContentSuccessToast, setShowContentSuccessToast] = useState(false);
  const [showBandwidthSuccessToast, setShowBandwidthSuccessToast] = useState(false);
  const [showAddUrlModal, setShowAddUrlModal] = useState(null);
  const [newUrl, setNewUrl] = useState("");
  const [customUrls, setCustomUrls] = useState({});
  const [domainsModal, setDomainsModal] = useState(null); // { categoryId, name, domains: [] }
  const [loadingBlockedState, setLoadingBlockedState] = useState(false);
  const [contentControlsInitialized, setContentControlsInitialized] = useState(false);
  const [bandwidthApplyLoading, setBandwidthApplyLoading] = useState({}); // { groupId: boolean }
  const [bandwidthClearLoading, setBandwidthClearLoading] = useState({}); // { groupId: boolean }
  
  // Simple domain request queue to prevent SSH server overload
  const domainRequestQueue = useRef([]);
  const isProcessingDomainQueue = useRef(false);
  
  // New state for per-category group toggles
  const [categoryGroupToggles, setCategoryGroupToggles] = useState({}); // { categoryId: { groupId: boolean } }
  
  // Store original toggle state for change detection
  const [originalToggles, setOriginalToggles] = useState({});

  // Database Rules State
  const [bandwidthRules, setBandwidthRules] = useState({}); // { groupId: { download_limit_mbps, upload_limit_mbps, is_active, description } }
  
  // Scheduled Tasks State
  const [scheduledTasks, setScheduledTasks] = useState([]);
  const [scheduledTasksLoading, setScheduledTasksLoading] = useState(false);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
  const [newTask, setNewTask] = useState({
    type: 'content', // 'content' or 'bandwidth'
    groupId: '',
    categories: [], // for content blocking
    downloadMbps: '', // for bandwidth limiting
    uploadMbps: '', // for bandwidth limiting
    startTime: '22:00', // when rule becomes active
    endTime: '08:00', // when rule becomes inactive
    days: [0, 1, 2, 3, 4, 6], // 0=Sunday, 1=Monday, etc. Default all days except Friday
    enabled: true
  });
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


  // Simple domain request queue processor - only for domain requests
  const processDomainQueue = async () => {
    if (isProcessingDomainQueue.current) {
      return;
    }
    
    isProcessingDomainQueue.current = true;
    
    try {
      while (domainRequestQueue.current.length > 0) {
        const request = domainRequestQueue.current.shift();
        try {
          const result = await request.execute();
          request.resolve(result);
        } catch (error) {
          request.reject(error);
        }
        
        // Simple delay between domain requests
        if (domainRequestQueue.current.length > 0) {
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      }
    } finally {
      isProcessingDomainQueue.current = false;
    }
  };

  // Helper function to queue ONLY domain requests
  const queueDomainRequest = async (description, executeFunction) => {
    return new Promise((resolve, reject) => {
      const request = {
        description,
        execute: executeFunction,
        resolve,
        reject
      };
      
      domainRequestQueue.current.push(request);
      
      if (!isProcessingDomainQueue.current) {
        processDomainQueue();
      }
    });
  };

       // Load groups from backend (needed for control functionality)
  useEffect(() => {
    const loadGroups = async () => {
      if (!routerId) return;
      
      try {
        console.log("🔄 [ControlPage] Loading groups from backend...");
        
        // Load groups directly
        const response = await deviceGroupsAPI.getGroups(routerId);
        console.log("🔍 [ControlPage] Raw groups response:", response);
        
        const backendGroups = response.data || [];
        console.log("🔍 [ControlPage] Backend groups:", backendGroups);
        
        // Map backend format to frontend format
        const mappedGroups = backendGroups.map(group => ({
          id: group.id,
          name: group.name,
          description: group.description,
          devices: (group.devices || []).map(device => ({
            id: device.id,
            ip: device.ip,
            mac: device.mac,
            hostname: device.hostname || device.device_name || 'Unknown Device',
            icon: getDeviceIcon(device.device_type || 'FaRegQuestionCircle'),
            type: device.device_type || 'Unknown'
          })),
          createdAt: group.created_at
        }));
        
        setGroups(mappedGroups);
        console.log("✅ [ControlPage] Loaded groups from backend:", mappedGroups.length);
        
      } catch (error) {
        console.error("❌ [ControlPage] Failed to load groups from backend:", error);
        // Set empty groups array on error
        setGroups([]);
      }
    };

    if (routerId) {
      console.log("🚀 [ControlPage] Router ID detected, starting to load groups...");
      loadGroups();
    } else {
      console.log("⏳ [ControlPage] Waiting for router ID...");
    }
  }, [routerId]);

  // Load scheduled tasks when component mounts or routerId changes
  useEffect(() => {
    if (routerId) {
      loadScheduledTasks();
    }
  }, [routerId]);

  // Load scheduled tasks from backend
  const loadScheduledTasks = async () => {
    if (!routerId) {
      console.log('⏳ [ScheduledTasks] Waiting for router ID...');
      return;
    }
    
    try {
      setScheduledTasksLoading(true);
      console.log('🔄 [ScheduledTasks] Loading scheduled tasks...');
      
      const response = await scheduledTasksAPI.listTasks(routerId);
      const tasks = response?.data?.tasks || [];
      
      console.log('✅ [ScheduledTasks] Loaded tasks:', tasks);
      setScheduledTasks(tasks);
      
    } catch (error) {
      console.error('❌ [ScheduledTasks] Failed to load scheduled tasks:', error);
      setScheduledTasks([]);
    } finally {
      setScheduledTasksLoading(false);
    }
  };

  // Scheduled Tasks Functions
  const handleCreateScheduledTask = async () => {
    if (!routerId || !newTask.groupId) {
      console.error('Missing required data for task creation');
      return;
    }

    const { type, groupId, startTime, endTime, days } = newTask;
    
    // Parse times
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    
    // Check if rule spans midnight (start time > end time)
    const spansMidnight = startHour > endHour || (startHour === endHour && startMin > endMin);
    
    // Calculate days for end task if spanning midnight
    const endTaskDays = spansMidnight ? days.map(day => (day + 1) % 7) : days;
    
    try {
      setScheduledTasksLoading(true);
      
      if (type === 'content') {
        if (!newTask.categories || newTask.categories.length === 0) {
          console.error('No categories selected for content blocking');
          return;
        }
        
        console.log('🔄 Creating content blocking tasks...');
        console.log('📅 Days for start task:', days);
        console.log('📅 Days for end task:', endTaskDays);
        console.log('⏰ Rule spans midnight:', spansMidnight);
        
        // Create activate task (set_devices_rules)
        const activateResponse = await scheduledTasksAPI.createTask(
          routerId, 
          "agh", 
          "set_devices_rules", 
          {
            group_id: groupId,
            categories: newTask.categories
          },
          startHour, 
          startMin, 
          days
        );
        
        console.log('✅ Activate task created:', activateResponse);
        const activateTaskId = activateResponse?.data?.id;
        
        // Create deactivate task (clear_devices_rules) with adjusted days if spanning midnight
        const deactivateResponse = await scheduledTasksAPI.createTask(
          routerId, 
          "agh", 
          "clear_devices_rules", 
          {
            group_id: groupId
          },
          endHour, 
          endMin, 
          endTaskDays
        );
        
        console.log('✅ Deactivate task created:', deactivateResponse);
        const deactivateTaskId = deactivateResponse?.data?.id;
        
        // Log the task pair for reference
        console.log('📋 Task pair created:', {
          type: 'content',
          groupId,
          categories: newTask.categories,
          activateTaskId,
          deactivateTaskId,
          timeRange: `${startTime}-${endTime}`,
          spansMidnight,
          startDays: days,
          endDays: endTaskDays
        });
        
      } else if (type === 'bandwidth') {
        if (!newTask.downloadMbps || !newTask.uploadMbps) {
          console.error('Missing bandwidth values');
          return;
        }
        
        console.log('🔄 Creating bandwidth limiting tasks...');
        console.log('📅 Days for start task:', days);
        console.log('📅 Days for end task:', endTaskDays);
        console.log('⏰ Rule spans midnight:', spansMidnight);
        
        // Create apply limits task
        const applyResponse = await scheduledTasksAPI.createTask(
          routerId, 
          "bandwidth", 
          "apply_group_limits", 
          {
            group_id: groupId,
            download_mbps: parseFloat(newTask.downloadMbps),
            upload_mbps: parseFloat(newTask.uploadMbps)
          },
          startHour, 
          startMin, 
          days
        );
        
        console.log('✅ Apply limits task created:', applyResponse);
        const applyTaskId = applyResponse?.data?.id;
        
        // Create remove limits task with adjusted days if spanning midnight
        const removeResponse = await scheduledTasksAPI.createTask(
          routerId, 
          "bandwidth", 
          "delete_group_limits", 
          {
            group_id: groupId
          },
          endHour, 
          endMin, 
          endTaskDays
        );
        
        console.log('✅ Remove limits task created:', removeResponse);
        const removeTaskId = removeResponse?.data?.id;
        
        // Log the task pair for reference
        console.log('📋 Task pair created:', {
          type: 'bandwidth',
          groupId,
          downloadMbps: newTask.downloadMbps,
          uploadMbps: newTask.uploadMbps,
          applyTaskId,
          removeTaskId,
          timeRange: `${startTime}-${endTime}`,
          spansMidnight,
          startDays: days,
          endDays: endTaskDays
        });
      }
      
      // Refresh task list and close modal
      await loadScheduledTasks();
      setShowCreateTaskModal(false);
      
      // Reset form
      setNewTask({
        type: 'content',
        groupId: '',
        categories: [],
        downloadMbps: '',
        uploadMbps: '',
        startTime: '22:00',
        endTime: '08:00',
        days: [0, 1, 2, 3, 4, 6],
        enabled: true,
        description: ''
      });
      
      console.log('✅ Scheduled tasks created successfully');
      
    } catch (error) {
      console.error('❌ Failed to create scheduled tasks:', error);
      // TODO: Show user-friendly error message
    } finally {
      setScheduledTasksLoading(false);
    }
  };



  const handleToggleScheduledTask = async (rule) => {
    if (!rule || !rule.taskIds || rule.taskIds.length === 0) {
      console.error('No task IDs provided for toggle');
      return;
    }
    
    const newEnabledState = !rule.enabled;
    console.log('🔄 Toggling scheduled rule:', rule.id, 'to', newEnabledState ? 'enabled' : 'disabled');
    
    // Optimistic update: Update UI immediately
    setScheduledTasks(prevTasks => 
      prevTasks.map(task => 
        rule.taskIds.includes(task.id) 
          ? { ...task, enabled: newEnabledState }
          : task
      )
    );
    
    try {
      // Toggle all tasks in the rule (usually 2 for paired tasks, 1 for individual)
      for (const taskId of rule.taskIds) {
        await scheduledTasksAPI.toggleTask(taskId, newEnabledState);
        console.log('✅ Toggled task:', taskId, 'to', newEnabledState ? 'enabled' : 'disabled');
      }
      
      console.log('✅ Scheduled rule toggled successfully');
      
    } catch (error) {
      console.error('❌ Failed to toggle scheduled rule:', error);
      
      // Revert optimistic update on error
      setScheduledTasks(prevTasks => 
        prevTasks.map(task => 
          rule.taskIds.includes(task.id) 
            ? { ...task, enabled: !newEnabledState } // Revert to original state
            : task
        )
      );
      
      // TODO: Show user-friendly error message
    }
  };

  const handleDeleteScheduledTask = async (rule) => {
    if (!rule || !rule.taskIds || rule.taskIds.length === 0) {
      console.error('No task IDs provided for deletion');
      return;
    }
    
    try {
      console.log('🔄 Deleting scheduled rule:', rule.id, 'with tasks:', rule.taskIds);
      
      // Delete all tasks in the rule (usually 2 for paired tasks, 1 for individual)
      for (const taskId of rule.taskIds) {
        await scheduledTasksAPI.deleteTask(taskId);
        console.log('✅ Deleted task:', taskId);
      }
      
      console.log('✅ Scheduled rule deleted successfully');
      
      // Refresh task list
      await loadScheduledTasks();
      
    } catch (error) {
      console.error('❌ Failed to delete scheduled rule:', error);
      // TODO: Show user-friendly error message
    }
  };

  // Helper function to refresh categories (clears cache and reloads)
  const refreshCategories = () => {
    try {
      localStorage.removeItem('netpilot_categories');
      setContentCategories([]);
      console.log("🔄 [ControlPage] Categories cache cleared, will reload on next render");
    } catch (error) {
      console.warn('Failed to clear categories cache:', error);
    }
  };

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

    // Get domain counts for each category SEQUENTIALLY to avoid overwhelming the SSH server
    const categoriesWithCounts = [];
    
    console.log(`🔄 [ControlPage] Starting SEQUENTIAL domain fetching for ${categoryNames.length} categories...`);
    
         for (let i = 0; i < categoryNames.length; i++) {
       const categoryId = categoryNames[i];
       console.log(`🔄 [ControlPage] Fetching domains for category ${i + 1}/${categoryNames.length}: ${categoryId}`);
       
       try {
         // Get domain count for this category - using the simple domain queue
         const domainResponse = await queueDomainRequest(`Fetching domains for ${categoryId}`, () => 
           aghAPI.getCategoryDomains(routerId, categoryId)
         );
        const domainCount = domainResponse.data?.count || 0;
        
        console.log(`✅ [ControlPage] Category ${categoryId}: ${domainCount} domains fetched`);
        
        categoriesWithCounts.push({
          id: categoryId,
          name: nameMap[categoryId] || categoryId.replace(/__/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          // Don't store icon functions in localStorage - we'll handle icons based on ID
          blocked: false, // Default all categories to allowed
          sites: domainCount,
          description: descriptionMap[categoryId] || `${categoryId.replace(/__/g, ' ').replace(/_/g, ' ')} category`,
        });
        
      } catch (error) {
        console.warn(`❌ [ControlPage] Failed to get domain count for category ${categoryId}:`, error);
        // Add category with default count if domain fetch fails
        categoriesWithCounts.push({
          id: categoryId,
          name: nameMap[categoryId] || categoryId.replace(/__/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          // Don't store icon functions in localStorage - we'll handle icons based on ID
          blocked: false, // Default all categories to allowed
          sites: 0,
          description: descriptionMap[categoryId] || `${categoryId.replace(/__/g, ' ').replace(/_/g, ' ')} category`,
        });
      }
    }
    
    console.log(`✅ [ControlPage] Completed SEQUENTIAL domain fetching for all ${categoriesWithCounts.length} categories`);
    return categoriesWithCounts;
  };

       // Load AGH categories dynamically from backend
  useEffect(() => {
    let isMounted = true; // Prevent state updates if component unmounts
    
    const loadCategories = async () => {
      if (!routerId) {
        console.log("⏳ [ControlPage] Waiting for routerId...", { routerId: !!routerId });
        return;
      }

      // Check if we have cached categories and they're not empty
      // Also check if cached categories have the problematic icon functions - if so, refresh
      const cachedCategories = contentCategories;
      if (cachedCategories && cachedCategories.length > 0) {
        // Check if any category has an icon function (which causes React errors)
        const hasIconFunctions = cachedCategories.some(cat => typeof cat.icon === 'function');
        if (hasIconFunctions) {
          console.log("🔄 [ControlPage] Cached categories have function icons, clearing cache and reloading...");
          try {
            localStorage.removeItem('netpilot_categories');
            setContentCategories([]);
          } catch (error) {
            console.warn('Failed to clear categories cache:', error);
          }
        } else {
          console.log("📦 [ControlPage] Using cached categories from localStorage:", cachedCategories.length, "categories");
          return;
        }
      }

      console.log("🚀 [ControlPage] Starting to load categories from API...");
      setCategoriesLoading(true);
      setCategoriesError(null);
      
      try {
        console.log("🔄 [ControlPage] Loading AGH categories from backend...");
        
        // Get category names from backend2 → commands server
        const categoriesResponse = await aghAPI.getCategories(routerId);
        const categoryNames = categoriesResponse.data?.categories || [];
        
        console.log("✅ [ControlPage] Received categories from API:", categoryNames);
        
        if (categoryNames.length === 0) {
          console.warn("⚠️ [ControlPage] No categories found, using empty array");
          if (isMounted) {
            setContentCategories([]);
          }
          return;
        }

        // Map category names to UI format with domain counts
        console.log("🔄 [ControlPage] Fetching domain counts for categories...");
        const uiCategories = await mapApiCategoriesToUI(categoryNames);
        
        console.log("✅ [ControlPage] Categories mapped to UI format:", uiCategories.length, "categories");
        if (isMounted) {
          setContentCategories(uiCategories);
          
          // Save categories to localStorage for future use
          try {
            localStorage.setItem('netpilot_categories', JSON.stringify(uiCategories));
            console.log("💾 [ControlPage] Categories saved to localStorage");
          } catch (error) {
            console.warn('Failed to save categories to localStorage:', error);
          }
        }
        
      } catch (error) {
        console.error("❌ [ControlPage] Failed to load AGH categories:", error);
        if (isMounted) {
          setCategoriesError(`Failed to load categories: ${error.message}`);
          // Fallback to empty array on error
          setContentCategories([]);
        }
      } finally {
        if (isMounted) {
          setCategoriesLoading(false);
        }
      }
    };

    loadCategories();
    
    // Cleanup function to prevent state updates after unmount
    return () => {
      isMounted = false;
    };
  }, [routerId]);

    // Load database rules when groups change
  useEffect(() => {
    const loadDatabaseRules = async () => {
      if (!routerId) return;

      setRulesLoading(true);
      setRulesError(null);
      
      try {
        console.log("🔄 [ControlPage] Loading database rules...");
        
        // Load bandwidth rules directly
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
        
        // Load content control rules directly
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
        
        console.log("✅ [ControlPage] Database rules loaded:", {
          bandwidth: Object.keys(bandwidthLookup).length,
          content: Object.keys(contentLookup).length
        });
        
      } catch (error) {
        console.error("❌ [ControlPage] Failed to load database rules:", error);
        setRulesError(`Failed to load rules: ${error.message}`);
        
        // Fallback to empty objects on error
        setBandwidthRules({});
        setContentControlRules({});
      } finally {
        setRulesLoading(false);
      }
    };

    loadDatabaseRules();
  }, [routerId]);

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
      console.log("🔄 [ControlPage] Creating new category:", createCategoryForm.name);
              console.log("🔧 [ControlPage] Sanitized name:", sanitizedCategoryName);
              console.log("📋 [ControlPage] Domains:", createCategoryForm.domains);

      // Call the API to create the category (use sanitized name)
      const response = await aghAPI.createCategory(routerId, sanitizedCategoryName, createCategoryForm.domains);
      
              console.log("✅ [ControlPage] Category created successfully:", response);

      // Close modal and reset form
      setShowCreateCategoryModal(false);
      resetCreateCategoryForm();

      // Add the new category to existing list instead of reloading all
              console.log("🔄 [ControlPage] Adding new category to list...");
      
      try {
                 // Get domain count for the new category - using the simple domain queue
         const domainResponse = await queueDomainRequest(`Creating new category: ${sanitizedCategoryName}`, () => 
           aghAPI.getCategoryDomains(routerId, sanitizedCategoryName)
         );
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
        console.log("✅ [ControlPage] New category added to list:", newCategory.name);
        
      } catch (error) {
        console.warn("⚠️ [ControlPage] Failed to get domain count for new category, using fallback");
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
      setShowContentSuccessToast(true);
      setTimeout(() => setShowContentSuccessToast(false), 3000);

    } catch (error) {
              console.error("❌ [ControlPage] Failed to create category:", error);
      alert(`Failed to create category: ${error.message}`);
    } finally {
      setCreateCategoryForm(prev => ({ ...prev, isSubmitting: false }));
    }
  };









  // Content Controls Handlers
  const handleContentToggle = (categoryId, groupId) => {
    // Prevent toggling before initialization is complete
    if (!contentControlsInitialized) {
      console.log("⚠️ Content controls not yet initialized, ignoring toggle");
      return;
    }
    
    console.log(`🔄 Toggling category ${categoryId} for group ${groupId}`);
    setCategoryGroupToggles((prev) => ({
      ...prev,
      [categoryId]: {
        ...(prev[categoryId] || {}),
        [groupId]: !(prev[categoryId]?.[groupId] || false)
      }
    }));
  };

  // Consolidated initialization: categories → database rules → groups → toggles
  useEffect(() => {
    const initializeContentControls = async () => {
      // Prevent multiple initializations
      if (contentControlsInitialized) {
        console.log("🔒 Content controls already initialized, skipping");
        return;
      }

      // Step 1: Ensure we have categories
      if (contentCategories.length === 0) {
        console.log("⏳ Waiting for categories to load...");
        setContentControlsInitialized(false);
        return;
      }

      // Step 2: Ensure we have loaded database rules (rules loading is complete)
      if (rulesLoading) {
        console.log("⏳ Waiting for database rules to finish loading...");
        return;
      }

      // Step 3: Handle case with no groups gracefully
      if (groups.length === 0) {
        console.log("ℹ️ No groups found. Initializing content controls with empty groups.");
        // Initialize empty toggles and mark as initialized so UI can render empty state
        setCategoryGroupToggles({});
        setOriginalToggles({});
        setContentControlsInitialized(true);
        return;
      }

      console.log("🔄 Initializing content controls with enforced order...");

      // Step 4: Initialize toggles structure with groups and load current state
      console.log("📋 All prerequisites ready, loading toggles...");
      await loadCurrentBlockedState();
      
      // Mark as initialized
      setContentControlsInitialized(true);
      console.log("✅ Content controls initialization complete");
    };

    initializeContentControls();
  }, [contentCategories, contentControlRules, rulesLoading, groups, contentControlsInitialized]);

  // Get summary of pending changes
  const getChangesSummary = () => {
    const summary = {};
    
    Object.keys(categoryGroupToggles).forEach(categoryId => {
      const category = contentCategories.find(c => c.id === categoryId);
      if (category) {
        const blockedGroups = [];
        const unblockedGroups = [];
        
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          const currentValue = categoryGroupToggles[categoryId]?.[groupId] || false;
          const originalValue = originalToggles[categoryId]?.[groupId] || false;
          
          if (currentValue !== originalValue) {
            const group = groups.find(g => g.id === groupId);
            if (group) {
              if (currentValue) {
                blockedGroups.push(group.name); // Newly blocked
              } else {
                unblockedGroups.push(group.name); // Newly unblocked
              }
            }
          }
        });
        
        if (blockedGroups.length > 0 || unblockedGroups.length > 0) {
          summary[category.name] = {
            blocked: blockedGroups,
            unblocked: unblockedGroups
          };
        }
      }
    });
    
    return summary;
  };

  // Check if there are any pending changes
  const hasPendingChanges = () => {
    return Object.keys(categoryGroupToggles).some(categoryId => 
      Object.keys(categoryGroupToggles[categoryId]).some(groupId => {
        const currentValue = categoryGroupToggles[categoryId]?.[groupId] || false;
        const originalValue = originalToggles[categoryId]?.[groupId] || false;
        return currentValue !== originalValue; // Compare current vs original state
      })
    );
  };

  // Update hasContentChanges when categoryGroupToggles change (only after initialization)
  useEffect(() => {
    if (contentControlsInitialized) {
      setHasContentChanges(hasPendingChanges());
    }
  }, [categoryGroupToggles, contentControlsInitialized]);

  // Reset all toggles to original state
  const resetAllToggles = () => {
    setCategoryGroupToggles(originalToggles); // Reset to original state, not all false
  };

  // Reset toggles to loaded state from database
  const resetToLoadedState = () => {
    const loadedToggles = {};
    contentCategories.forEach(category => {
      loadedToggles[category.id] = {};
      groups.forEach(group => {
        // Check if this group has rules for this category
        const hasRules = contentControlRules[group.id]?.blocked_categories?.includes(category.id);
        loadedToggles[category.id][group.id] = hasRules || false;
      });
    });
    setCategoryGroupToggles(loadedToggles);
    setOriginalToggles(loadedToggles);
  };

  // Clear all rules and reset toggles to false
  const clearAllRules = async () => {
    if (!routerId) return;
    
    setContentClearLoading(true);
    try {
      // Clear all rules from database
      for (const group of groups) {
        try {
          await contentControlRulesAPI.deleteGroupRules(routerId, group.id);
          console.log(`✅ Database rules cleared for group ${group.id}`);
        } catch (dbError) {
          console.error(`❌ Failed to clear database rules for group ${group.id}:`, dbError);
          // Continue with other groups even if one fails
        }
      }

      // Clear AGH rules from actual devices
      for (const group of groups) {
        if (group.devices && group.devices.length > 0) {
          const devicesToClear = group.devices.map(d => ({ ip: d.ip, mac: d.mac })).filter(d => d.ip);
          if (devicesToClear.length > 0) {
            try {
                             await aghAPI.clearDevicesRules(routerId, devicesToClear);
              console.log(`✅ AGH rules cleared for group ${group.id}:`, devicesToClear.length, 'devices');
            } catch (aghError) {
              console.error(`❌ Failed to clear AGH rules for group ${group.id}:`, aghError);
              // Continue with other groups even if one fails
            }
          }
        }
      }

      // Reset all toggles to false
      const resetToggles = {};
      contentCategories.forEach(category => {
        resetToggles[category.id] = {};
        groups.forEach(group => {
          resetToggles[category.id][group.id] = false;
        });
      });
      setCategoryGroupToggles(resetToggles);
      
      // Update original state to all false
      setOriginalToggles(resetToggles);
      
      // Clear local content control rules
      setContentControlRules({});
      
      // Reset change state
      setHasContentChanges(false);
      
      console.log("✅ All content control rules cleared from database, devices, and UI");
    } catch (error) {
      console.error("❌ Failed to clear all rules:", error);
      alert("Failed to clear all rules. Please try again.");
    } finally {
      setContentClearLoading(false);
    }
  };

  // Load current blocked state from database and backend
  const loadCurrentBlockedState = async () => {
    if (!routerId || groups.length === 0 || contentCategories.length === 0) {
      console.log("❌ loadCurrentBlockedState: Missing prerequisites", {
        routerId: !!routerId,
        groupsCount: groups.length,
        categoriesCount: contentCategories.length
      });
      return;
    }
    
    console.log("🔄 loadCurrentBlockedState: Starting with data:", {
      routerId,
      groupsCount: groups.length,
      categoriesCount: contentCategories.length,
      databaseRulesCount: Object.keys(contentControlRules).length,
      contentControlRules: contentControlRules
    });
    
    setLoadingBlockedState(true);
    try {
      // Initialize fresh toggles structure with all groups
      const updatedToggles = {};
      contentCategories.forEach(category => {
        updatedToggles[category.id] = {};
        groups.forEach(group => {
          updatedToggles[category.id][group.id] = false; // Start with false
        });
      });
      
      console.log("🔧 Initialized toggles structure with", contentCategories.length, "categories and", groups.length, "groups");
      
      // Load toggles from database rules
      let rulesAppliedCount = 0;
      for (const group of groups) {
        const groupRules = contentControlRules[group.id];
        if (groupRules && groupRules.blocked_categories) {
          console.log(`📋 Group ${group.name} (${group.id}) has rules:`, groupRules.blocked_categories);
          contentCategories.forEach(category => {
            if (updatedToggles[category.id]) {
              const shouldBlock = groupRules.blocked_categories.includes(category.id);
              updatedToggles[category.id][group.id] = shouldBlock;
              if (shouldBlock) {
                rulesAppliedCount++;
                console.log(`✅ Setting toggle ON: ${category.name} → ${group.name}`);
              }
            }
          });
        } else {
          console.log(`📋 Group ${group.name} (${group.id}) has no database rules`);
        }
      }
      
      console.log(`🎯 Applied ${rulesAppliedCount} rules from database`);
      
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
      
      console.log("🔄 Setting final toggles state:", updatedToggles);
      setCategoryGroupToggles(updatedToggles);
      
      // Save original state for change detection
      console.log("💾 Saving original state for change detection");
      setOriginalToggles(updatedToggles);
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

    setContentApplyLoading(true);
    try {
      // Build a map of ONLY CHANGED groups to their blocked categories
      const changedGroupCategoryMap = {};
      const allGroupCategoryMap = {};
      
      // First, build complete current state map
      Object.keys(categoryGroupToggles).forEach(categoryId => {
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          if (categoryGroupToggles[categoryId][groupId]) {
            if (!allGroupCategoryMap[groupId]) {
              allGroupCategoryMap[groupId] = [];
            }
            allGroupCategoryMap[groupId].push(categoryId);
          }
        });
      });

      console.log(`🔍 Current toggle state:`, categoryGroupToggles);
      console.log(`🔍 Built allGroupCategoryMap:`, allGroupCategoryMap);

      // Identify groups with changes by comparing current vs original state
      const changedGroups = new Set();
      Object.keys(categoryGroupToggles).forEach(categoryId => {
        Object.keys(categoryGroupToggles[categoryId]).forEach(groupId => {
          const currentValue = categoryGroupToggles[categoryId]?.[groupId] || false;
          const originalValue = originalToggles[categoryId]?.[groupId] || false;
          if (currentValue !== originalValue) {
            changedGroups.add(groupId);
          }
        });
      });

      // Build map for only changed groups
      changedGroups.forEach(groupId => {
        changedGroupCategoryMap[groupId] = allGroupCategoryMap[groupId] || [];
      });

      console.log(`📊 Total groups: ${Object.keys(allGroupCategoryMap).length}, Changed groups: ${changedGroups.size}`);
      console.log(`📊 allGroupCategoryMap:`, allGroupCategoryMap);
      console.log(`📊 changedGroups:`, Array.from(changedGroups));

      // Save rules to database for ALL groups (to maintain consistency)
      // Also handle groups that should have rules deleted (groups that were in original state but not in current)
      const allGroupsToProcess = new Set([
        ...Object.keys(allGroupCategoryMap),
        ...Array.from(changedGroups)
      ]);

      console.log(`📊 All groups to process:`, Array.from(allGroupsToProcess));

      for (const groupId of allGroupsToProcess) {
        const categoryIds = allGroupCategoryMap[groupId] || [];
        console.log(`💾 Processing group ${groupId}:`, categoryIds);
        
        if (categoryIds.length > 0) {
          try {
            const groupName = groups.find(g => g.id === groupId)?.name || 'Unknown Group';
            console.log(`💾 Saving rules for group ${groupId} (${groupName}):`, categoryIds);
            await contentControlRulesAPI.setGroupRules(routerId, groupId, {
              blocked_categories: categoryIds,
              description: `Content control rules for ${groupName}`,
              is_active: true
            });
            console.log(`✅ Database rules saved for group ${groupId}:`, categoryIds);
          } catch (dbError) {
            console.error(`❌ Failed to save database rules for group ${groupId}:`, dbError);
            throw dbError;
          }
        } else {
          // If group has no categories, delete the rules instead of saving empty array
          try {
            console.log(`🗑️ Deleting rules for group ${groupId} (no categories)`);
            await contentControlRulesAPI.deleteGroupRules(routerId, groupId);
            console.log(`✅ Database rules deleted for group ${groupId} (no categories)`);
          } catch (dbError) {
            console.error(`❌ Failed to delete database rules for group ${groupId}:`, dbError);
            throw dbError;
          }
        }
      }

      // Apply rules to actual devices via AGH API - ONLY FOR CHANGED GROUPS
      for (const [groupId, categoryIds] of Object.entries(changedGroupCategoryMap)) {
        const group = groups.find(g => g.id === groupId);
        if (group && Array.isArray(group.devices)) {
          const devicesToApply = group.devices.map(d => ({ ip: d.ip, mac: d.mac })).filter(d => d.ip);
          if (devicesToApply.length > 0) {
            if (categoryIds.length > 0) {
                             // Apply rules when categories exist
               await aghAPI.setDevicesRules(routerId, devicesToApply, categoryIds);
              console.log(`🚀 AGH rules applied for CHANGED group ${groupId}:`, devicesToApply.length, 'devices, categories:', categoryIds);
            } else {
                             // Clear rules when no categories
               await aghAPI.clearDevicesRules(routerId, devicesToApply);
              console.log(`🧹 AGH rules cleared for CHANGED group ${groupId}:`, devicesToApply.length, 'devices');
            }
          }
        }
      }

      // Update local state - handle both additions and deletions
      setContentControlRules(prev => {
        const updated = { ...prev };
        
        // Handle groups with rules (add/update)
        Object.entries(allGroupCategoryMap).forEach(([groupId, categoryIds]) => {
          if (categoryIds.length > 0) {
            updated[groupId] = {
              blocked_categories: categoryIds,
              is_active: true,
              description: `Content control rules for ${groups.find(g => g.id === groupId)?.name || 'Unknown Group'}`
            };
          }
        });
        
        // Handle groups that had rules deleted (remove from state)
        changedGroups.forEach(groupId => {
          if (!allGroupCategoryMap[groupId] || allGroupCategoryMap[groupId].length === 0) {
            delete updated[groupId];
          }
        });
        
        return updated;
      });

      setHasContentChanges(false);
      setShowContentSuccessToast(true);
      setTimeout(() => setShowContentSuccessToast(false), 3000);
      
      // Update original state to current state after successful apply
      setOriginalToggles(categoryGroupToggles);

      console.log("Content controls applied successfully to database and devices");
    } catch (error) {
      console.error("Failed to apply content changes:", error);
      alert(error?.message || "Failed to apply changes. Please try again.");
    } finally {
      setContentApplyLoading(false);
    }
  };



  const openDomainsModal = async (categoryId, name) => {
    if (!routerId) return;
    try {
             // Use the simple domain queue for sequential processing
       const res = await queueDomainRequest(`Managing domains for ${categoryId}`, () => 
         aghAPI.getCategoryDomains(routerId, categoryId)
       );
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
      
              console.log(`✅ [ControlPage] Updated domain count for ${domainsModal.categoryId}: ${newDomainCount} domains`);
      
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
      console.log("🔄 [ControlPage] Deleting category:", categoryId);
      
      // Call the API to delete the category
      await aghAPI.deleteCategory(routerId, categoryId);
      
              console.log("✅ [ControlPage] Category deleted successfully:", categoryId);
      
      // Remove the category from the local state
      setContentCategories(prev => prev.filter(cat => cat.id !== categoryId));
      
      // Show success message
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);
      
    } catch (error) {
              console.error("❌ [ControlPage] Failed to delete category:", error);
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

    setBandwidthApplyLoading(prev => ({ ...prev, [groupId]: true }));
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
      // Show bandwidth success toast
      setShowBandwidthSuccessToast(true);
      setTimeout(() => setShowBandwidthSuccessToast(false), 3000);
    } catch (error) {
      console.error("Failed to apply bandwidth changes:", error);
      alert("Failed to apply changes. Please try again.");
    } finally {
      setBandwidthApplyLoading(prev => ({ ...prev, [groupId]: false }));
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
    setBandwidthClearLoading(prev => ({ ...prev, [groupId]: true }));
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
    } finally {
      setBandwidthClearLoading(prev => ({ ...prev, [groupId]: false }));
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

     // Show loading state while waiting for router ID
   if (!routerId) {
     return (
       <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
         <div className="text-center py-20">
           <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-6"></div>
           <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-2">
             Connecting to Router...
           </h2>
           <p className="text-gray-600 dark:text-gray-300">
             Please wait while we establish a connection to your router
           </p>
         </div>
       </div>
     );
   }

   return (
     <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
       
       
       {/* Header */}
       <div className="mb-8">
         <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
           Control Center
         </h1>
         <p className="text-gray-600 dark:text-gray-300">
           Manage content controls and bandwidth limits for your network
         </p>
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

          {/* Bandwidth rules status hidden per request */}

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
             <div className="space-y-4">
               {/* Loading indicator */}
               <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                 <div className="flex items-center gap-3">
                   <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                   <div className="flex-1">
                     <p className="text-blue-700 dark:text-blue-300 font-medium">
                       Loading bandwidth rules...
                     </p>
                     <p className="text-blue-600 dark:text-blue-400 text-sm mt-1">
                       Please wait while we load your bandwidth settings
                     </p>
                   </div>
                 </div>
               </div>
               
               {/* Loading skeleton table */}
               <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
                 <div className="p-6">
                   <div className="animate-pulse">
                     <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-1/4 mb-4"></div>
                     <div className="space-y-3">
                       {[...Array(3)].map((_, index) => (
                         <div key={index} className="flex items-center space-x-4">
                           <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4"></div>
                           <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/6"></div>
                           <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/6"></div>
                           <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
                           <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
                         </div>
                       ))}
                     </div>
                   </div>
                 </div>
               </div>
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
                      Limit
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
                              className={`w-20 p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-800 dark:text-white text-sm [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${
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
                            disabled={!hasChanges || bandwidthApplyLoading[group.id]}
                            className={`px-3 py-1 rounded text-sm transition-colors flex items-center gap-1 ${
                              hasChanges && !bandwidthApplyLoading[group.id]
                                ? "bg-blue-500 hover:bg-blue-600 text-white"
                                : "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                            }`}
                          >
                            {bandwidthApplyLoading[group.id] ? (
                              <>
                                <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                Applying...
                              </>
                            ) : (
                              "Apply"
                            )}
                          </button>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => handleClearGroupLimits(group.id)}
                            disabled={bandwidthClearLoading[group.id]}
                            className={`px-3 py-1 rounded text-sm transition-colors flex items-center gap-1 ${
                              bandwidthClearLoading[group.id]
                                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                                : "bg-gray-200 hover:bg-gray-300"
                            }`}
                          >
                            {bandwidthClearLoading[group.id] ? (
                              <>
                                <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                Clearing...
                              </>
                            ) : (
                              "Clear"
                            )}
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
                className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
                onClick={resetToLoadedState}
                disabled={contentApplyLoading || contentClearLoading}
                className="bg-yellow-500 hover:bg-yellow-600 dark:bg-yellow-600 dark:hover:bg-yellow-500 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                <FaUndo className="text-sm" />
                Reset to Loaded
              </button>
              <button
                onClick={clearAllRules}
                disabled={contentClearLoading}
                className="bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-500 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                {contentClearLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Clearing...
                  </>
                ) : (
                  <>
                    <FaTimes className="text-sm" />
                    Clear All Rules
                  </>
                )}
              </button>
              {hasContentChanges && (
                <button
                  onClick={handleApplyContentChanges}
                  disabled={contentApplyLoading}
                  className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  {contentApplyLoading ? (
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
                          total + Object.keys(categoryGroupToggles[categoryId]).reduce((catTotal, groupId) => {
                            const currentValue = categoryGroupToggles[categoryId]?.[groupId] || false;
                            const originalValue = originalToggles[categoryId]?.[groupId] || false;
                            return catTotal + (currentValue !== originalValue ? 1 : 0);
                          }, 0), 0
                        )}
                      </span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Content controls status hidden per request */}

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
                {Object.entries(getChangesSummary()).map(([categoryName, changes]) => (
                  <div key={categoryName} className="flex items-start gap-2">
                    <span className="font-medium">• {categoryName}:</span>
                    <span>
                      {changes.blocked.length > 0 && `Block for ${changes.blocked.join(', ')}`}
                      {changes.blocked.length > 0 && changes.unblocked.length > 0 && ' | '}
                      {changes.unblocked.length > 0 && `Unblock for ${changes.unblocked.join(', ')}`}
                    </span>
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
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                  ⚠️ Database Rules Error
                </span>
                <span className="text-xs text-orange-600 dark:text-orange-400">
                  {rulesError}
                </span>
              </div>
              <p className="text-orange-600 dark:text-orange-400 text-xs mt-1">
                Some features may not work properly. Rules will be saved locally only.
              </p>
            </div>
          )}
          
          {/* Combined active rules banner hidden per request */}
          
          {/* Content Controls Initialization Status */}
          {!categoriesLoading && !rulesLoading && !contentControlsInitialized && (
            <div className="mb-4 p-4 bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-700 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <div className="flex-1">
                  <p className="text-blue-700 dark:text-blue-300 font-medium">
                    Initializing Content Controls...
                  </p>
                  <p className="text-blue-600 dark:text-blue-400 text-sm mt-1">
                    Loading current rules and preparing toggles for all groups
                  </p>
                </div>
              </div>
            </div>
          )}
          
                     {categoriesLoading || rulesLoading ? (
             <div className="space-y-4">
               {/* Simple loading indicator */}
               <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                 <div className="flex items-center gap-3">
                   <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                   <div className="flex-1">
                     <p className="text-blue-700 dark:text-blue-300 font-medium">
                       Loading content controls...
                     </p>
                     <p className="text-blue-600 dark:text-blue-400 text-sm mt-1">
                       Please wait while we load your content control settings
                     </p>
                   </div>
                 </div>
               </div>
               
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 {/* Loading skeleton cards */}
                 {[...Array(6)].map((_, index) => (
                   <div
                     key={index}
                     className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border animate-pulse"
                   >
                     <div className="flex items-center justify-between mb-4">
                       <div className="flex items-center gap-3">
                         <div className="w-8 h-8 bg-gray-300 dark:bg-gray-800 rounded"></div>
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
              const categoryUrls = customUrls[category.id] || [];
              
              // Get the appropriate icon component based on category ID
              const getIconComponent = (categoryId) => {
                switch (categoryId) {
                  case 'adult_gambling':
                    return <EighteenPlusIcon className="text-lg" />;
                  case 'social_media':
                    return <FaUsers className="text-lg" />;
                  case 'entertainment':
                    return <FaTv className="text-lg" />;
                  case 'gaming':
                    return <FaGamepad className="text-lg" />;
                  case 'shopping':
                    return <FaShoppingCart className="text-lg" />;
                  default:
                    return <FaCog className="text-lg" />;
                }
              };
              
              return (
                <div
                  key={category.id}
                  className="border rounded-lg p-4 transition-all hover:shadow-md border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-700"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-800 dark:text-blue-300">
                        {getIconComponent(category.id)}
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
                            <label className={`relative inline-flex items-center ${!contentControlsInitialized ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                              <input
                                type="checkbox"
                                checked={categoryGroupToggles[category.id]?.[group.id] || false}
                                onChange={() => handleContentToggle(category.id, group.id)}
                                disabled={!contentControlsInitialized}
                                className="sr-only peer"
                              />
                              <div className={`w-9 h-5 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 dark:after:border-gray-500 after:border after:rounded-full after:h-4 after:w-4 after:transition-all ${
                                !contentControlsInitialized 
                                  ? 'bg-gray-300 dark:bg-gray-500' 
                                  : 'bg-gray-200 dark:bg-gray-600 peer-checked:bg-red-600 dark:peer-checked:bg-red-500'
                              }`}></div>
                            </label>
                          </div>
                        ))}
                        {groups.length === 0 && (
                          <div className="text-center py-4">
                            <FaUsers className="text-gray-400 dark:text-gray-500 mx-auto mb-2 text-lg" />
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                              No groups available
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              No groups available for content controls
                            </p>
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

                  <div className="flex items-center">
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
                  </div>
                </div>
              );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* Scheduled Tasks Section */}
      <div className="mb-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white">Scheduled Tasks</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">Schedule automatic content blocking and bandwidth limits</p>
            </div>
            <button 
              onClick={() => setShowCreateTaskModal(true)}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 transition-colors flex items-center gap-2"
            >
              <FaPlus />
              Create Task
            </button>
          </div>
          
          {/* Tasks by Group */}
          <div className="space-y-6">
            {groups.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <FaUsers className="mx-auto text-4xl mb-2 opacity-50" />
                <p>No device groups available. Create groups first to schedule tasks.</p>
              </div>
            ) : (
              groups.map((group) => {
                // Ensure scheduledTasks is an array and group them into user-friendly rules
                const tasksArray = Array.isArray(scheduledTasks) ? scheduledTasks : [];
                const groupedRules = groupTasksIntoRules(tasksArray);
                const groupRules = groupedRules.filter(rule => 
                  rule.groupId === group.id
                );
                
                return (
                  <div key={group.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <FaUsers className="text-blue-500 dark:text-blue-400" />
            <div>
                          <h3 className="font-semibold text-gray-800 dark:text-white">{group.name}</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{group.devices?.length || 0} devices</p>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {groupRules.length} scheduled {groupRules.length === 1 ? 'rule' : 'rules'}
                      </div>
                    </div>

                    {groupRules.length === 0 ? (
                      <div className="text-center py-4 text-gray-400 dark:text-gray-500 text-sm">
                        No scheduled tasks for this group
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {groupRules.map((rule) => (
                          <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-2">
                                {rule.type === 'content' ? (
                                  <FaGlobe className="text-red-500 dark:text-red-400" />
                                ) : (
                                  <FaDownload className="text-green-500 dark:text-green-400" />
                                )}
                                <div>
                                  <div className="font-medium text-gray-800 dark:text-white">
                                    {rule.type === 'content' ? 'Content Blocking' : 'Bandwidth Limit'}
                                    {rule.isInterval 
                                      ? ` (Every ${rule.intervalMinutes >= 60 
                                          ? `${Math.floor(rule.intervalMinutes / 60)} hour${Math.floor(rule.intervalMinutes / 60) > 1 ? 's' : ''}${rule.intervalMinutes % 60 ? ` ${rule.intervalMinutes % 60}min` : ''}` 
                                          : `${rule.intervalMinutes} minute${rule.intervalMinutes > 1 ? 's' : ''}`
                                        })` 
                                      : rule.endTime 
                                        ? ` (${rule.startTime} - ${rule.endTime})` 
                                        : ` (${rule.startTime})`
                                    }
                                  </div>
                                  <div className="text-sm text-gray-600 dark:text-gray-400">
                                    {rule.days && rule.days.length > 0 ? 
                                      rule.days.map(day => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day]).join(', ') :
                                      'Daily'
                                    }
                                    {rule.endTime && rule.spansMidnight && (
                                      <span className="ml-2 px-2 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                                        Overnight
                                      </span>
                                    )}
                                    {rule.type === 'content' && rule.categories && (
                                      <span> • {rule.categories.join(', ')}</span>
                                    )}
                                    {rule.type === 'bandwidth' && rule.downloadMbps && (
                                      <span> • {rule.downloadMbps}↓/{rule.uploadMbps}↑ Mbps</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className={`px-2 py-1 rounded text-xs font-medium ${
                                rule.enabled 
                                  ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' 
                                  : 'bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200'
                              }`}>
                                {rule.enabled ? 'Active' : 'Disabled'}
                              </div>
                              <button
                                onClick={() => handleToggleScheduledTask(rule)}
                                className={`p-1 rounded transition-colors ${
                                  rule.enabled 
                                    ? 'text-green-500 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900' 
                                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600'
                                }`}
                                title={rule.enabled ? 'Disable task' : 'Enable task'}
                              >
                                {rule.enabled ? <FaToggleOn /> : <FaToggleOff />}
                              </button>
                              <button
                                onClick={() => handleDeleteScheduledTask(rule)}
                                className="p-1 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                                title="Delete task"
                              >
                                <FaTrash />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {scheduledTasksLoading && (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              Loading scheduled tasks...
            </div>
          )}
        </div>
      </div>

      {/* Success Toasts */}
      {showContentSuccessToast && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <FaCheck />
          Content rule applied successfully!
        </div>
      )}
      {showBandwidthSuccessToast && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <FaCheck />
          Bandwidth rule applied successfully!
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateTaskModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Create Scheduled Task</h3>
              <button
                onClick={() => setShowCreateTaskModal(false)}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                <FaTimes />
              </button>
            </div>

            <div className="space-y-6">
              {/* Task Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Task Type</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setNewTask(prev => ({ ...prev, type: 'content' }))}
                    className={`p-4 rounded-lg border-2 transition-colors ${
                      newTask.type === 'content'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                        : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <FaGlobe className="mx-auto mb-2 text-2xl text-blue-500" />
                    <div className="font-medium">Content Control</div>
                    <div className="text-sm opacity-75">Block/allow website categories</div>
                  </button>
                  <button
                    onClick={() => setNewTask(prev => ({ ...prev, type: 'bandwidth' }))}
                    className={`p-4 rounded-lg border-2 transition-colors ${
                      newTask.type === 'bandwidth'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                        : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <FaDownload className="mx-auto mb-2 text-2xl text-blue-500" />
                    <div className="font-medium">Bandwidth Control</div>
                    <div className="text-sm opacity-75">Apply/remove speed limits</div>
                  </button>
                </div>
              </div>

              {/* Group Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Device Group</label>
                <select
                  value={newTask.groupId}
                  onChange={(e) => setNewTask(prev => ({ ...prev, groupId: e.target.value }))}
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
                >
                  <option value="">Select a group</option>
                  {groups.map(group => (
                    <option key={group.id} value={group.id}>
                      {group.name} ({group.devices?.length || 0} devices)
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="text-blue-600 dark:text-blue-400 mt-1">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
                      How it works
                    </h4>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      {newTask.type === 'content' 
                        ? 'This will automatically block the selected categories during the specified time period, and unblock them outside of those hours.'
                        : 'This will automatically apply bandwidth limits during the specified time period, and remove them outside of those hours.'
                      }
                    </p>
                  </div>
                </div>
              </div>

              {/* Content Categories (if content type) */}
              {newTask.type === 'content' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Categories to Block During Scheduled Hours</label>
                  <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-gray-50 dark:bg-gray-700">
                    {(() => {
                      console.log('🔍 [ScheduledTasks] Rendering categories:', contentCategories.length, contentCategories);
                      return contentCategories.length === 0 ? (
                        <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
                          Loading categories...
                        </div>
                      ) : (
                        contentCategories.map(category => {
                          console.log('🔍 [ScheduledTasks] Rendering category:', category);
                          return (
                        <label key={category.id} className="flex items-center gap-3 p-2 hover:bg-gray-100 dark:hover:bg-gray-600 rounded cursor-pointer">
              <input 
                            type="checkbox"
                            checked={newTask.categories.includes(category.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setNewTask(prev => ({ ...prev, categories: [...prev.categories, category.id] }));
                              } else {
                                setNewTask(prev => ({ ...prev, categories: prev.categories.filter(c => c !== category.id) }));
                              }
                            }}
                            className="rounded border-gray-300 dark:border-gray-500 text-blue-600 focus:ring-blue-500"
                          />
                          <div className="flex items-center gap-2">
                            <span className="text-xl text-blue-500">
                              {(() => {
                                // Handle icons based on category ID since localStorage can't store functions
                                switch (category.id) {
                                  case 'adult_gambling':
                                    return <EighteenPlusIcon />;
                                  case 'social_media':
                                    return <FaUsers />;
                                  case 'entertainment':
                                    return <FaTv />;
                                  case 'gaming':
                                    return <FaGamepad />;
                                  case 'shopping':
                                    return <FaShoppingCart />;
                                  default:
                                    return <FaCog />;
                                }
                              })()}
                            </span>
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{category.name || category.displayName}</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">({category.sites || category.domainCount} domains)</span>
                          </div>
                        </label>
                          );
                        })
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Bandwidth Limits (if bandwidth type) */}
              {newTask.type === 'bandwidth' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Bandwidth Limits During Scheduled Hours</label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Download Speed (Mbps)</label>
                      <input
                type="number" 
                min="0.1" 
                step="0.1" 
                        value={newTask.downloadMbps}
                        onChange={(e) => setNewTask(prev => ({ ...prev, downloadMbps: e.target.value }))}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., 10"
                        required
              />
            </div>
            <div>
                      <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Upload Speed (Mbps)</label>
              <input 
                type="number" 
                min="0.1" 
                step="0.1" 
                        value={newTask.uploadMbps}
                        onChange={(e) => setNewTask(prev => ({ ...prev, uploadMbps: e.target.value }))}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="e.g., 5"
                        required
              />
            </div>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    These limits will be applied during the scheduled time period. Outside of these hours, normal speeds will be restored.
                  </p>
                </div>
              )}

                            {/* Time Range */}
            <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Active Time Period</label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                      {newTask.type === 'content' ? 'Block From' : 'Limit From'}
                    </label>
                    <CustomTimeInput
                      value={newTask.startTime}
                      onChange={(value) => setNewTask(prev => ({ ...prev, startTime: value }))}
                      placeholder="22:00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                      {newTask.type === 'content' ? 'Unblock At' : 'Restore At'}
                    </label>
                    <CustomTimeInput
                      value={newTask.endTime}
                      onChange={(value) => setNewTask(prev => ({ ...prev, endTime: value }))}
                      placeholder="08:00"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  {newTask.type === 'content' 
                    ? 'Content will be blocked from start time to end time, then automatically unblocked.'
                    : 'Bandwidth limits will be active from start time to end time, then automatically removed.'
                  }
                </p>
              </div>

              {/* Days Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Days of Week</label>
                <div className="flex flex-wrap gap-2">
                  {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((day, index) => (
              <button 
                      key={day}
                      onClick={() => {
                        if (newTask.days.includes(index)) {
                          setNewTask(prev => ({ ...prev, days: prev.days.filter(d => d !== index) }));
                        } else {
                          setNewTask(prev => ({ ...prev, days: [...prev.days, index].sort() }));
                        }
                      }}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        newTask.days.includes(index)
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      {day.slice(0, 3)}
              </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button 
                  onClick={() => setShowCreateTaskModal(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateScheduledTask}
                  disabled={!newTask.groupId || (newTask.type === 'content' && newTask.categories.length === 0) || (newTask.type === 'bandwidth' && (!newTask.downloadMbps || !newTask.uploadMbps))}
                  className="px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
                >
                  Create Scheduled Task
              </button>
            </div>
          </div>
        </div>
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
              <button className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-white hover:bg-gray-400 dark:hover:bg-gray-500 rounded transition-colors" onClick={() => setDomainsModal(null)}>Cancel</button>
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

export default ControlPage;
