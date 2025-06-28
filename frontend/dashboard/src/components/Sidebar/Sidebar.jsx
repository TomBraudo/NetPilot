import React from "react";
import { links } from "../../constants";
import LinkItem from "./LinkItem";
import { useAuth } from "../../context/AuthContext";

const Sidebar = ({ isSidebarOpen }) => {
  const { user, logout } = useAuth();

  return (
    <aside
      className={`fixed top-0 left-0 z-40 w-64 h-screen bg-white border-r border-gray-200 
      dark:bg-gray-800 dark:border-gray-700 transition-transform duration-300 ease-in-out
      ${
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      } lg:translate-x-0`}
    >
      <div className="h-full flex flex-col">
        {/* Menu Items */}
        <div className="flex-1 px-3 pb-4 overflow-y-auto pt-20">
          <ul className="space-y-2 font-medium">
            {links.map((link, index) => (
              <LinkItem key={index} {...link} />
            ))}
          </ul>
        </div>

        {/* User Info Section */}
        {user && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center space-x-3">
              {/* User Avatar */}
              <div className="flex-shrink-0">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="w-10 h-10 rounded-full"
                  />
                ) : (
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold text-sm">
                      {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                    </span>
                  </div>
                )}
              </div>

              {/* User Details */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user.email}
                </p>
              </div>

              {/* Logout Button */}
              <button
                onClick={logout}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
