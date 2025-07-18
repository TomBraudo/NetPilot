import React, { useState } from 'react';
import { Router } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const RouterIdPopup = ({ isOpen, onClose, onConfirm }) => {
  const [routerId, setRouterId] = useState('');
  const { saveRouterIdToBackend } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (routerId.trim()) {
      await saveRouterIdToBackend(routerId.trim());
      if (onConfirm) onConfirm(routerId.trim());
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center justify-center mb-4">
          <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full">
            <Router className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white text-center mb-2">
          Router ID Required
        </h2>
        
        <p className="text-gray-600 dark:text-gray-400 text-center mb-4">
          Please enter your Router ID to connect to your network device.
        </p>
        
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-4">
          <p className="text-sm text-blue-800 dark:text-blue-400 text-center">
            💡 Your Router ID is displayed in your NetPilot agent app
          </p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="routerId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Router ID
            </label>
            <input
              type="text"
              id="routerId"
              value={routerId}
              onChange={(e) => setRouterId(e.target.value)}
              placeholder="Enter your Router ID"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              required
            />
          </div>
          
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!routerId.trim()}
              className={`flex-1 px-4 py-2 rounded-md transition-colors ${
                routerId.trim()
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              }`}
            >
              Apply
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RouterIdPopup; 