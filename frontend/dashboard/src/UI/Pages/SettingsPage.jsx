import React, { useState } from "react";
import { Router, Settings, Edit } from "lucide-react";
import RouterIdPopup from "../../components/RouterIdPopup";
import { useAuth } from "../../context/AuthContext";

const SettingsPage = () => {
  const [showRouterIdPopup, setShowRouterIdPopup] = useState(false);
  const { routerId, saveRouterIdToBackend } = useAuth();

  const handleChangeRouterId = () => {
    setShowRouterIdPopup(true);
  };

  const handleRouterIdConfirm = async (newRouterId) => {
    console.log('Settings page: Router ID change confirmed:', newRouterId);
    // The saveRouterIdToBackend function will handle all the backend logic
    // and update the context state automatically
    setShowRouterIdPopup(false);
  };

  const handleClosePopup = () => {
    setShowRouterIdPopup(false);
  };

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
              Settings
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Configure your application preferences and settings
            </p>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Router Settings Section */}
            <div className="border-b border-gray-200 dark:border-gray-700 pb-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Router Configuration
              </h2>
              
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <Router className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        Router ID
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {routerId ? `Current: ${routerId}` : 'No router ID configured'}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleChangeRouterId}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    {routerId ? 'Change Router ID' : 'Set Router ID'}
                  </button>
                </div>
                
                <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                  💡 Your Router ID connects this dashboard to your NetPilot agent. Changing it will replace your current router connection.
                </div>
              </div>
            </div>

            {/* Future Settings Sections */}
            <div className="text-center py-8">
              <div className="text-gray-400 dark:text-gray-500">
                <Settings className="mx-auto h-12 w-12 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  More Settings Coming Soon
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Additional configuration options will be available here in future updates.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Router ID Popup */}
      <RouterIdPopup 
        isOpen={showRouterIdPopup}
        onClose={handleClosePopup}
        onConfirm={handleRouterIdConfirm}
        cancelButtonText="Cancel"
        showAsLogout={false}
      />
    </div>
  );
};

export default SettingsPage; 