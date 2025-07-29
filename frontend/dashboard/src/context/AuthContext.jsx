import React, { createContext, useContext, useState, useEffect } from 'react';

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
      localStorage.removeItem('routerId');
      window.location.href = '/';
    }
  };

  const setRouterIdValue = (id) => {
    setRouterId(id);
    localStorage.setItem('routerId', id);
    setShowRouterIdPopup(false);
    setRouterIdChecked(true);
  };

  const clearRouterId = () => {
    setRouterId(null);
    localStorage.removeItem('routerId');
    setShowRouterIdPopup(false);
    setRouterIdChecked(false);
  };

  // Fetch routerId from backend after login
  const fetchRouterIdFromBackend = async (retries = 3) => {
    console.log('=== Starting fetchRouterIdFromBackend ===');
    console.log('API_BASE_URL:', API_BASE_URL);
    
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
            setRouterId(data.data.routerId);
            localStorage.setItem('routerId', data.data.routerId);
            setShowRouterIdPopup(false);
            setRouterIdChecked(true);
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
        
        console.log('Setting router ID in state:', id);
        setRouterId(id);
        console.log('Saving router ID to localStorage:', id);
        localStorage.setItem('routerId', id);
        console.log('Hiding router ID popup');
        setShowRouterIdPopup(false);
        setRouterIdChecked(true);
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
    // Check for login success parameter
    const urlParams = new URLSearchParams(window.location.search);
    const loginSuccess = urlParams.get('login');
    
    console.log('URL params:', Object.fromEntries(urlParams.entries()));
    
    if (loginSuccess === 'success') {
      console.log('Login success detected, checking auth status...');
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Enhanced retry logic with proper sequencing
      const handleLoginSuccess = async () => {
        let authenticated = false;
        
        // First, ensure authentication is successful
        for (let i = 0; i < 5; i++) {
          console.log(`Auth check attempt ${i + 1}/5`);
          
          // Exponential backoff: 1s, 2s, 4s, 8s, 16s
          const delay = Math.pow(2, i) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          
          const userData = await checkAuthStatus();
          
          if (userData) {
            console.log('User authenticated successfully');
            authenticated = true;
            break;
          }
          
          if (i === 4) {
            console.error('Authentication failed after all retries');
            login(); // Redirect to login again
            return;
          }
        }
        
        // If authenticated, check for existing router ID
        if (authenticated) {
          console.log('Checking for existing router ID...');
          
          // Additional wait to ensure backend session is fully synchronized
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          const hasRouterId = await fetchRouterIdFromBackend();
          
          if (!hasRouterId) {
            console.log('No router ID found, will show popup');
            // The popup will be shown by the next useEffect
          } else {
            console.log('Router ID found, popup will not be shown');
          }
        }
      };
      
      handleLoginSuccess();
    } else {
      console.log('No login success, checking auth status normally...');
      const initializeAuth = async () => {
        const userData = await checkAuthStatus();
        if (userData) {
          // Check for existing router ID for returning users
          await fetchRouterIdFromBackend();
        }
      };
      initializeAuth();
    }
  }, []);

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

  const value = {
    user,
    loading,
    login,
    logout,
    checkAuthStatus,
    routerId,
    showRouterIdPopup,
    setRouterIdValue,
    clearRouterId,
    setShowRouterIdPopup,
    saveRouterIdToBackend,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 