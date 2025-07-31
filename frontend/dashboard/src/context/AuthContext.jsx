import React, { createContext, useContext, useState, useEffect } from 'react';
import { sessionAPI } from '../constants/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [routerId, setRouterId] = useState(() => {
    return localStorage.getItem('routerId') || null;
  });
  const [showRouterIdPopup, setShowRouterIdPopup] = useState(false);
  const [routerIdChecked, setRouterIdChecked] = useState(false); // Track if we've checked for router ID
  const [sessionStarted, setSessionStarted] = useState(false); // Track if session has been started
  const [authFlowCompleted, setAuthFlowCompleted] = useState(false); // Track if auth flow has been completed

  const API_BASE_URL = 'http://localhost:5000';

  const checkAuthStatus = async () => {
    try {
      console.log('Checking auth status...');
      const response = await fetch(`${API_BASE_URL}/me`, {
        credentials: 'include', // Include cookies for session
      });
      
      console.log('Auth response status:', response.status);
      
      if (response.ok) {
        const userData = await response.json();
        console.log('User data received:', userData);
        setUser(userData);
        return userData; // Return user data for chaining
      } else {
        console.log('Auth failed, setting user to null');
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    // Redirect to backend login endpoint
    window.location.href = `${API_BASE_URL}/login`;
  };

  const logout = async () => {
    try {
      console.log('Logging out...');
      
      // End commands server session before logout if we have a router ID
      if (routerId) {
        try {
          console.log('=== ENDING COMMANDS SERVER SESSION ON LOGOUT ===');
          console.log('🔌 Router ID:', routerId);
          console.log('📡 API endpoint: /api/network/session/end');
          console.log('⏰ Timestamp:', new Date().toISOString());
          
          const startTime = performance.now();
          await sessionAPI.end(routerId);
          const endTime = performance.now();
          
          console.log('✅ Commands server session ended successfully');
          console.log('⏱️  Response time:', Math.round(endTime - startTime), 'ms');
          console.log('=== SESSION END COMPLETED ===');
        } catch (sessionError) {
          console.error('❌ FAILED TO END COMMANDS SERVER SESSION');
          console.error('📊 Error details:', sessionError);
          console.error('🔍 Error message:', sessionError.message);
          console.error('🔧 Router ID used:', routerId);
          console.error('⚠️  Continuing with logout despite session end failure...');
          // Don't block logout if session end fails
        }
      } else {
        console.log('⚠️  No router ID available - skipping session end');
      }
      
      const response = await fetch(`${API_BASE_URL}/logout`, {
        credentials: 'include',
        method: 'POST',
      });
      
      if (response.ok) {
        console.log('Logout successful');
        // Clear user state and router ID
        setUser(null);
        setRouterId(null);
        setShowRouterIdPopup(false);
        setRouterIdChecked(false);
        setSessionStarted(false);
        setAuthFlowCompleted(false); // Reset flag for re-authentication
        localStorage.removeItem('routerId');
        // Redirect to dashboard
        window.location.href = '/';
      } else {
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('Error logging out:', error);
      // Even if logout fails, clear local state and redirect
      setUser(null);
      setRouterId(null);
      setShowRouterIdPopup(false);
      setRouterIdChecked(false);
      setSessionStarted(false);
      setAuthFlowCompleted(false); // Reset flag for re-authentication
      localStorage.removeItem('routerId');
      window.location.href = '/';
    }
  };

  const setRouterIdValue = async (id) => {
    console.log('🎯 TRIGGER: Router ID set by user - implementing controlled flow...');
    console.log('📍 Context: setRouterIdValue() called with ID:', id);
    console.log('🔧 User state available:', !!user, '(should be true for popup usage)');
    
    // CONTROLLED FLOW: Save router ID first, THEN start session
    
    // Step 4A: Save router ID to localStorage and confirm
    const saveSuccess = saveRouterIdToLocalStorage(id);
    if (!saveSuccess) {
      console.error('❌ Failed to save router ID to localStorage in setRouterIdValue');
      return;
    }
    
    // Update other state after successful save
    setShowRouterIdPopup(false);
    setRouterIdChecked(true);
    
    // Step 4B: Start session ONLY after router ID is confirmed saved
    const sessionSuccess = await startSessionAfterRouterIdSaved(id, null);
    if (!sessionSuccess) {
      console.error('❌ Session start failed in setRouterIdValue, but router ID is saved');
    }
  };

  const clearRouterId = () => {
    setRouterId(null);
    localStorage.removeItem('routerId');
    setShowRouterIdPopup(false);
    setRouterIdChecked(false);
    setSessionStarted(false);
  };

  // Save router ID to localStorage and confirm it's saved
  const saveRouterIdToLocalStorage = (routerId) => {
    console.log('💾 STEP 4A: Saving router ID to localStorage...');
    console.log('🔧 Router ID to save:', routerId);
    
    // Save to state
    setRouterId(routerId);
    
    // Save to localStorage
    localStorage.setItem('routerId', routerId);
    
    // Confirm it's saved by reading it back
    const savedRouterId = localStorage.getItem('routerId');
    const stateMatch = routerId === savedRouterId;
    
    console.log('💾 LocalStorage save verification:');
    console.log('  - Original router ID:', routerId);
    console.log('  - Retrieved from localStorage:', savedRouterId);
    console.log('  - Save successful:', stateMatch);
    console.log('✅ STEP 4A COMPLETE: Router ID saved to localStorage');
    
    return stateMatch;
  };

  // Start commands server session ONLY after router ID is confirmed saved
  const startSessionAfterRouterIdSaved = async (routerId, userData) => {
    console.log('🚀 STEP 4B: Starting commands server session...');
    console.log('🔧 Router ID confirmed in localStorage:', localStorage.getItem('routerId'));
    console.log('🔧 Router ID parameter:', routerId);
    console.log('🔧 User data available:', !!userData);
    
    // Double-check router ID is in localStorage
    const savedRouterId = localStorage.getItem('routerId');
    if (savedRouterId !== routerId) {
      console.error('❌ Router ID mismatch!');
      console.error('  - Expected:', routerId);
      console.error('  - In localStorage:', savedRouterId);
      return false;
    }
    
    console.log('✅ Router ID verification passed, proceeding with session start...');
    const success = await startCommandsServerSession(routerId, userData);
    
    if (success) {
      console.log('✅ STEP 4B COMPLETE: Commands server session started successfully');
      setSessionStarted(true); // Mark session as started
    } else {
      console.error('❌ STEP 4B FAILED: Commands server session start failed');
    }
    
    return success;
  };

  // Start session with commands server (critical for router operations)
  const startCommandsServerSession = async (routerId, userData = null) => {
    // Use provided userData or fall back to state (for race condition fix)
    const activeUser = userData || user;
    
    console.log('=== STARTING COMMANDS SERVER SESSION ===');
    console.log('User authenticated:', !!activeUser);
    console.log('User data:', activeUser);
    console.log('Router ID provided:', routerId);
    console.log('Timestamp:', new Date().toISOString());
    console.log('🔧 Using provided userData:', !!userData, '(race condition fix)');

    if (!activeUser || !routerId) {
      console.error('❌ Cannot start commands server session - missing prerequisites:');
      console.error('  - User authenticated:', !!activeUser);
      console.error('  - Router ID provided:', !!routerId);
      console.error('  - State user:', !!user);
      console.error('  - Provided userData:', !!userData);
      return false;
    }

    try {
      console.log('📡 Calling sessionAPI.start() with parameters:');
      console.log('  - routerId:', routerId);
      console.log('  - restart:', false);
      console.log('  - API endpoint: /api/network/session/start');
      
      const startTime = performance.now();
      const result = await sessionAPI.start(routerId, false); // restart=false for normal start
      const endTime = performance.now();
      
      console.log('✅ Commands server session started successfully!');
      console.log('📊 Session start response:', result);
      console.log('⏱️  Response time:', Math.round(endTime - startTime), 'ms');
      console.log('🎯 Session ID from response:', result?.sessionId || 'Not provided');
      console.log('🌐 Router reachable:', result?.routerReachable || 'Unknown');
      console.log('🏗️  Infrastructure ready:', result?.infrastructureReady || 'Unknown');
      console.log('💬 Message:', result?.message || 'No message');
      console.log('=== SESSION START COMPLETED SUCCESSFULLY ===');
      
      return true;
    } catch (error) {
      console.error('❌ FAILED TO START COMMANDS SERVER SESSION');
      console.error('📊 Error details:', error);
      console.error('🔍 Error message:', error.message);
      console.error('🔍 Error stack:', error.stack);
      console.error('📡 API endpoint attempted: /api/network/session/start');
      console.error('🔧 Router ID used:', routerId);
      console.error('👤 User context:', user?.email || 'Unknown user');
      console.error('=== SESSION START FAILED ===');
      
      return false;
    }
  };

  // Fetch routerId from backend after login
  const fetchRouterIdFromBackend = async (retries = 3, userData = null) => {
    console.log('=== Starting fetchRouterIdFromBackend ===');
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('🔧 Received userData parameter:', !!userData, userData ? '(race condition fix active)' : '(fallback to state)');
    
    const requestUrl = `${API_BASE_URL}/api/settings/router-id`;
    
    for (let i = 0; i < retries; i++) {
      console.log(`Router ID fetch attempt ${i + 1}/${retries}`);
      console.log('Request URL:', requestUrl);
      console.log('Request method: GET');
      console.log('Credentials: include');
      
      try {
        console.log('Making fetch request...');
        const response = await fetch(requestUrl, {
          credentials: 'include',
        });
        
        console.log('Response received:');
        console.log('Response status:', response.status);
        console.log('Response status text:', response.statusText);
        
        if (response.ok) {
          console.log('Response is OK, parsing JSON...');
          const data = await response.json();
          console.log('Response data:', data);
          
          if (data.success && data.data && data.data.routerId) {
            console.log('Router ID found in response:', data.data.routerId);
            
            // DETERMINISTIC FLOW: Save router ID first, let the deterministic flow handle session start
            console.log('🎯 TRIGGER: Router ID loaded from backend - implementing deterministic flow...');
            console.log('📍 Context: fetchRouterIdFromBackend() success');
            
            // Step 4A: Save router ID to localStorage and confirm
            const saveSuccess = saveRouterIdToLocalStorage(data.data.routerId);
            if (!saveSuccess) {
              console.error('❌ Failed to save router ID to localStorage');
              return false;
            }
            
            // Update other state after successful save
            setShowRouterIdPopup(false);
            setRouterIdChecked(true);
            
            // Step 4B: Let the deterministic flow handle session start
            console.log('✅ Router ID saved successfully, deterministic flow will handle session start');
            
            console.log('=== fetchRouterIdFromBackend completed successfully ===');
            return true; // Success
          } else {
            console.log('No router ID found in response data');
            setRouterIdChecked(true);
            return false; // No router ID found
          }
        } else if (response.status === 401) {
          console.log('Authentication error, retrying...');
          if (i < retries - 1) {
            // Wait before retry for auth error
            await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
            continue;
          }
        } else if (response.status === 404) {
          console.log('Response status is 404 - No router ID found');
          setRouterIdChecked(true);
          return false; // No router ID found
        } else {
          console.error('Response is not OK and not 404/401');
          const errorText = await response.text();
          console.error('Error response text:', errorText);
          
          if (i < retries - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            continue;
          }
        }
      } catch (error) {
        console.error('Exception occurred in fetchRouterIdFromBackend:', error);
        if (i < retries - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
          continue;
        }
      }
    }
    
    console.error('=== fetchRouterIdFromBackend failed after all retries ===');
    setRouterIdChecked(true);
    return false; // Failed
  };

  // Save routerId to backend
  const saveRouterIdToBackend = async (id) => {
    console.log('=== Starting saveRouterIdToBackend ===');
    console.log('Input router ID:', id);
    console.log('API_BASE_URL:', API_BASE_URL);
    
    const requestUrl = `${API_BASE_URL}/api/settings/router-id`;
    const requestBody = { routerId: id };
    
    console.log('Request URL:', requestUrl);
    console.log('Request method: POST');
    console.log('Request body:', requestBody);
    console.log('Request headers:', { 'Content-Type': 'application/json' });
    console.log('Credentials: include');
    
    try {
      console.log('Making fetch request...');
      const response = await fetch(requestUrl, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      
      console.log('Response received:');
      console.log('Response status:', response.status);
      console.log('Response status text:', response.statusText);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        console.log('Response is OK, parsing JSON...');
        const responseData = await response.json();
        console.log('Response data:', responseData);
        
        console.log('Backend save successful, implementing deterministic flow...');
        
        // DETERMINISTIC FLOW: Save router ID first, let the deterministic flow handle session start
        console.log('🎯 TRIGGER: Router ID saved to backend - implementing deterministic flow...');
        console.log('📍 Context: saveRouterIdToBackend() success');
        console.log('🔧 User state available:', !!user, '(should be true for authenticated save)');
        
        // Step 4A: Save router ID to localStorage and confirm
        const saveSuccess = saveRouterIdToLocalStorage(id);
        if (!saveSuccess) {
          console.error('❌ Failed to save router ID to localStorage in saveRouterIdToBackend');
          return false;
        }
        
        // Update other state after successful save
        setShowRouterIdPopup(false);
        setRouterIdChecked(true);
        
        // Step 4B: Let the deterministic flow handle session start
        console.log('✅ Router ID saved successfully, deterministic flow will handle session start');
        
        console.log('=== saveRouterIdToBackend completed successfully ===');
        return true;
      } else {
        console.error('Response is not OK');
        console.error('Response status:', response.status);
        console.error('Response status text:', response.statusText);
        
        try {
          const errorData = await response.json();
          console.error('Error response data:', errorData);
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
          const errorText = await response.text();
          console.error('Error response text:', errorText);
        }
        
        console.error('=== saveRouterIdToBackend failed ===');
        return false;
      }
    } catch (error) {
      console.error('Exception occurred in saveRouterIdToBackend:', error);
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      console.error('=== saveRouterIdToBackend failed with exception ===');
      return false;
    }
  };

  useEffect(() => {
    if (authFlowCompleted) {
      console.log('🔧 Auth flow already completed, skipping initialization');
      return;
    }
    
    // Check for login success parameter
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');
    
    console.log('URL params:', Object.fromEntries(urlParams.entries()));
    
    if (loginSuccess === 'success') {
      console.log('Login success detected, checking auth status...');
      setAuthFlowCompleted(true); // Mark flow as started
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Enhanced retry logic with proper sequencing
      const handleLoginSuccess = async () => {
        let authenticatedUserData = null;
        
        console.log('🔄 STEP 1: Ensuring authentication is fully complete...');
        
        // First, ensure authentication is successful
        for (let i = 0; i < 5; i++) {
          console.log(`Auth check attempt ${i + 1}/5`);
          
          // Exponential backoff: 1s, 2s, 4s, 8s, 16s
          const delay = Math.pow(2, i) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          
          const userData = await checkAuthStatus();
          
          if (userData) {
            console.log('✅ User authenticated successfully');
            console.log('🔧 Storing userData for controlled flow:', userData);
            authenticatedUserData = userData;
            break;
          }
          
          if (i === 4) {
            console.error('❌ Authentication failed after all retries');
            login(); // Redirect to login again
            return;
          }
        }
        
        // Only proceed if we have authenticated user data
        if (authenticatedUserData) {
          console.log('🔄 STEP 2: Authentication FULLY complete, checking router ID...');
          
          // Additional wait to ensure backend session is fully synchronized
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          console.log('🔄 STEP 3: Fetching router ID from backend...');
          const hasRouterId = await fetchRouterIdFromBackend(3, authenticatedUserData);
          
          if (!hasRouterId) {
            console.log('⚠️  No router ID found, popup will be shown later');
            // The popup will be shown by the next useEffect
          } else {
            console.log('✅ Router ID found and session started successfully');
          }
        } else {
          console.error('❌ No authenticated user data available');
        }
      };
      
      handleLoginSuccess();
    } else {
      console.log('No login success, checking auth status normally...');
      setAuthFlowCompleted(true); // Mark flow as started
      
      const initializeAuth = async () => {
        const userData = await checkAuthStatus();
        if (userData) {
          console.log('🔧 Normal auth: Passing userData to fetchRouterIdFromBackend:', userData);
          // Check for existing router ID for returning users
          await fetchRouterIdFromBackend(3, userData);
        }
      };
      initializeAuth();
    }
  }, [authFlowCompleted]);

  // Show Router ID popup only when user is authenticated, no Router ID exists, and we've checked the backend
  useEffect(() => {
    console.log('Router ID popup decision:', {
      user: !!user,
      routerId: routerId,
      routerIdChecked: routerIdChecked,
      showRouterIdPopup: showRouterIdPopup
    });
    
    if (user && !routerId && routerIdChecked && !showRouterIdPopup) {
      console.log('Showing router ID popup - user authenticated but no router ID found');
      setShowRouterIdPopup(true);
    }
  }, [user, routerId, routerIdChecked]);

  // Deterministic session start flow - only after authentication is fully complete
  useEffect(() => {
    if (user && routerId && routerIdChecked && !sessionStarted) {
      console.log('🎯 DETERMINISTIC FLOW: User authenticated and router ID confirmed, starting session...');
      console.log('🔧 User:', user.email);
      console.log('🔧 Router ID:', routerId);
      console.log('🔧 Router ID Checked:', routerIdChecked);
      console.log('🔧 Session Started:', sessionStarted);
      
      // Start session only after both user and router ID are confirmed
      startSessionAfterRouterIdSaved(routerId, user);
    }
  }, [user, routerId, routerIdChecked, sessionStarted]);



  const value = {
    user,
    loading,
    login,
    logout,
    checkAuthStatus,
    routerId,
    showRouterIdPopup,
    sessionStarted,
    setRouterIdValue,
    clearRouterId,
    setShowRouterIdPopup,
    saveRouterIdToBackend,
    startCommandsServerSession,
    saveRouterIdToLocalStorage,
    startSessionAfterRouterIdSaved,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 