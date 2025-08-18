import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const AuthRedirectHandler = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, routerId, sessionStarted, showRouterIdPopup } = useAuth();
  const hasRedirected = useRef(false);

  // Simple debug log on every render
  console.log('🎯 AuthRedirectHandler render:', {
    user: !!user,
    routerId: !!routerId,
    sessionStarted,
    showRouterIdPopup,
    path: location.pathname,
    hasRedirected: hasRedirected.current
  });

  useEffect(() => {
    console.log('🔍 REDIRECT CHECK: Evaluating redirect conditions...');
    console.log('🔧 User:', !!user, user?.email);
    console.log('🔧 Router ID:', routerId);
    console.log('🔧 Session Started:', sessionStarted);
    console.log('🔧 Show Router ID Popup:', showRouterIdPopup);
    console.log('🔧 Current path:', location.pathname);
    console.log('🔧 Has redirected:', hasRedirected.current);
    
    // Do not auto-redirect or auto-scan after login
    // Users will manually navigate and trigger scans via the Scan button
  }, [user, routerId, sessionStarted, showRouterIdPopup, location.pathname, navigate]);

  // Reset redirect flag when user changes (for logout/login scenarios)
  useEffect(() => {
    if (!user) {
      hasRedirected.current = false;
    }
  }, [user]);

  // This component doesn't render anything
  return null;
};

export default AuthRedirectHandler;