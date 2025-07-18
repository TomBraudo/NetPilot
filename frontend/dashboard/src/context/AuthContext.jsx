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
      } else {
        console.log('Auth failed, setting user to null');
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setUser(null);
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
      localStorage.removeItem('routerId');
      window.location.href = '/';
    }
  };

  const setRouterIdValue = (id) => {
    setRouterId(id);
    localStorage.setItem('routerId', id);
    setShowRouterIdPopup(false);
  };

  const clearRouterId = () => {
    setRouterId(null);
    localStorage.removeItem('routerId');
    setShowRouterIdPopup(false);
  };

  // Fetch routerId from backend after login
  const fetchRouterIdFromBackend = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/settings/router-id`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data && data.data.routerId) {
          setRouterId(data.data.routerId);
          localStorage.setItem('routerId', data.data.routerId);
          setShowRouterIdPopup(false);
        } else {
          // No routerId found, show popup if user is logged in
          if (user) setShowRouterIdPopup(true);
        }
      } else if (response.status === 404) {
        // No routerId found, show popup if user is logged in
        if (user) setShowRouterIdPopup(true);
      } else {
        // Other errors
        console.error('Failed to fetch routerId from backend');
      }
    } catch (error) {
      console.error('Error fetching routerId from backend:', error);
    }
  };

  // Save routerId to backend
  const saveRouterIdToBackend = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/settings/router-id`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ routerId: id }),
      });
      if (response.ok) {
        setRouterId(id);
        localStorage.setItem('routerId', id);
        setShowRouterIdPopup(false);
      } else {
        console.error('Failed to save routerId to backend');
      }
    } catch (error) {
      console.error('Error saving routerId to backend:', error);
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
      // Check auth status after successful login with multiple retries
      const checkAuthWithRetry = async (retries = 3) => {
        for (let i = 0; i < retries; i++) {
          console.log(`Auth check attempt ${i + 1}/${retries}`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Increasing delay
          await checkAuthStatus();
          if (user) {
            console.log('User authenticated successfully');
            // Try to fetch routerId from backend before showing popup
            await fetchRouterIdFromBackend();
            break;
          }
        }
      };
      checkAuthWithRetry();
    } else {
      console.log('No login success, checking auth status normally...');
      checkAuthStatus();
      // Always try to fetch routerId from backend after checking auth
      fetchRouterIdFromBackend();
    }
  }, []);

  // Show Router ID popup when user is authenticated but no Router ID is set
  useEffect(() => {
    if (user && !routerId && !showRouterIdPopup) {
      setShowRouterIdPopup(true);
    }
  }, [user, routerId]);

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
    saveRouterIdToBackend, // <-- add this to context
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 