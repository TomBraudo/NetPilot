import React from "react";
import { FaMoon } from "react-icons/fa";
import { MdSunny } from "react-icons/md";
import { HiOutlineMenuAlt2 } from "react-icons/hi";
import colorLogo from "../../assets/color_logo2.png";
import whiteLogo from "../../assets/white_logo.png";

const Header = ({ darkMode, toggleDarkMode, toggleSidebar }) => {
  return (
    <div className="h-full flex items-center justify-between w-full">
      {/* Left side: Logo + Toggle (mobile) */}
      <div className="flex items-center gap-4">
        {/* Sidebar toggle on mobile */}
        <button
          onClick={toggleSidebar}
          className="lg:hidden p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
        >
          <HiOutlineMenuAlt2 className="text-xl" />
        </button>

        {/* Logo */}
        <div className="flex items-center gap-1">
          <img
            src={darkMode ? whiteLogo : colorLogo}
            alt="NetPilot Logo"
            className="h-8 w-8 object-contain"
          />
          <span className="text-xl font-semibold text-gray-900 dark:text-white">
            NetPilot
          </span>
        </div>
      </div>

      {/* Right side: Dark Mode toggle */}
      <button
        onClick={toggleDarkMode}
        className="p-2 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-white transition"
        title="Toggle dark mode"
      >
        {darkMode ? <MdSunny size={18} /> : <FaMoon size={16} />}
      </button>
    </div>
  );
};

export default Header;
