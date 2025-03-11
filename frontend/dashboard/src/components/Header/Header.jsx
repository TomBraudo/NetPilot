import React from "react";
import { FaMoon } from "react-icons/fa";
import { MdSunny } from "react-icons/md";
import { HiOutlineMenuAlt2 } from "react-icons/hi";

const Header = ({ darkMode, toggleDarkMode, toggleSidebar }) => {
  return (
    <nav
      className="fixed top-0 z-50 w-full bg-white border-b border-gray-200
      dark:bg-gray-800 dark:border-gray-700 transition-all duration-300"
    >
      <div className="px-3 py-3 lg:px-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {/* Sidebar Toggle Button (Visible on md and smaller) */}
            <button
              className="inline-flex items-center p-2 text-sm text-gray-500 rounded-lg md:inline-flex lg:hidden hover:bg-gray-100
              focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400
              dark:hover:bg-gray-700 dark:focus:ring-gray-600"
              onClick={toggleSidebar}
            >
              <HiOutlineMenuAlt2 className="text-2xl text-gray-700 dark:text-gray-300" />
            </button>

            {/* Logo + Title */}
            <a href="/" className="flex items-center ms-2 md:me-24">
              <img
                src={
                  darkMode
                    ? "/src/assets/white_logo.png"
                    : "/src/assets/color_logo2.png"
                }
                alt="NetPilot Logo"
                className="h-8 w-8 object-contain"
              />

              <span className="ml-2 text-xl font-semibold sm:text-2xl whitespace-nowrap dark:text-white text-gray-900">
                NetPilot
              </span>
            </a>
          </div>

          {/* Dark Mode Toggle Button */}
          <button
            className="dark:bg-slate-50 dark:text-slate-700 rounded-full p-2"
            onClick={toggleDarkMode}
          >
            {darkMode ? <MdSunny /> : <FaMoon />}
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Header;
