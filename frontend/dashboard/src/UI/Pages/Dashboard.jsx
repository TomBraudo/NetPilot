import { Wifi, ArrowRight } from "lucide-react";
import NetworkBackground from "../../components/NetworkBackground";
import ScanButton from "../../components/ScanButton";
import LoginButton from "../../components/LoginButton";
import RouterIdPopup from "../../components/RouterIdPopup";
import { useAuth } from "../../context/AuthContext";

function Dashboard() {
  const { 
    user, 
    loading, 
    checkAuthStatus, 
    routerId, 
    showRouterIdPopup, 
    setRouterIdValue, 
    setShowRouterIdPopup,
    logout
  } = useAuth();

  if (loading) {
    return (
      <div className="relative text-gray-500 bg-gray-100 dark:bg-gray-800 w-full h-screen overflow-hidden flex items-center justify-center">
        <NetworkBackground />
        <main className="max-w-2xl text-center relative z-10 px-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="relative text-gray-500 bg-gray-100 dark:bg-gray-800 w-full h-screen overflow-hidden flex items-center justify-center">
      <NetworkBackground />

      <main className="max-w-2xl text-center relative z-10 px-4">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-gray-900 dark:text-white">
          Who's using your Wi-Fi?
        </h1>

        <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 max-w-xl mx-auto">
          NetPilot lets you see, control, and manage every connected device
        </p>

        <div className="flex justify-center mb-12">
          {user && routerId ? (
            <ScanButton />
          ) : user ? (
            <div className="text-center">
              <div className="inline-flex items-center px-6 py-3 text-lg font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded-full">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-3"></div>
                Setting up your router connection...
              </div>
            </div>
          ) : (
            <LoginButton />
          )}
        </div>

        {/* Router ID Popup */}
        <RouterIdPopup 
          isOpen={showRouterIdPopup}
          onClose={logout}
          onConfirm={setRouterIdValue}
        />

        <div className="text-gray-400 dark:text-gray-300">
          <p className="mb-2">
            Note: NetPilot requires OpenWrt installed on your router.
          </p>
          <a
            href="https://www.youtube.com/watch?v=7cxiYmn3OTU"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-500 hover:text-blue-400 transition-colors group"
          >
            <span className="group-hover:underline">
              👉 Click here for a setup guide
            </span>
            <ArrowRight className="w-4 h-4 ml-1 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </a>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
