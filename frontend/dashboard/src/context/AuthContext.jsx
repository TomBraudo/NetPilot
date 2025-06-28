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
        // Clear user state
        setUser(null);
        // Redirect to dashboard
        window.location.href = '/';
      } else {
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('Error logging out:', error);
      // Even if logout fails, clear local state and redirect
      setUser(null);
      window.location.href = '/';
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
            break;
          }
        }
      };
      checkAuthWithRetry();
    } else {
      console.log('No login success, checking auth status normally...');
      checkAuthStatus();
    }
  }, []);

  const value = {
    user,
    loading,
    login,
    logout,
    checkAuthStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 