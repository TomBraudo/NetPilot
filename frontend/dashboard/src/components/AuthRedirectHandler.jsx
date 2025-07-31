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
    
    // Auto-redirect to scan page ONLY after successful authentication and session establishment
    // Session is REQUIRED for proper app functionality
    if (user && routerId && sessionStarted && !showRouterIdPopup && !hasRedirected.current) {
      // Only redirect if we're currently on the home page
      if (location.pathname === '/') {
        console.log('🚀 AUTO-REDIRECT: All conditions met, redirecting to scan page...');
        console.log('📝 Note: Session properly established, safe to redirect');
        
        hasRedirected.current = true;
        
        // Small delay to ensure all state is settled, then navigate with autoScan
        setTimeout(() => {
          console.log('✅ Executing redirect to /scan with autoScan enabled');
          navigate('/scan', { state: { autoScan: true } });
        }, 500);
      } else {
        console.log('❌ Not redirecting - not on home page');
      }
    } else {
      console.log('❌ Not redirecting - conditions not met:');
      console.log('  - User authenticated:', !!user);
      console.log('  - Router ID available:', !!routerId);
      console.log('  - Session started:', sessionStarted, '(REQUIRED for redirect)');
      console.log('  - Popup closed:', !showRouterIdPopup);
      console.log('  - Not already redirected:', !hasRedirected.current);
    }
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