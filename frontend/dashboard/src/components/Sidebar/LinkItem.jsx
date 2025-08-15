import React from "react";
import { NavLink } from "react-router-dom";

const LinkItem = ({ href, icon: Icon, text, badge }) => {
  return (
    <li>
      <NavLink
        to={href}
        className={({ isActive }) =>
          `flex items-center p-2 rounded-lg transition-colors ${
            isActive
              ? "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white"
              : "text-gray-900 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
          }`
        }
      >
        <Icon className="mr-3" />
        <span className="flex-1 me-3">{text}</span>
        {badge && (
          <span
            className={`inline-flex items-center justify-center px-2 ms-3 text-sm font-medium rounded-full ${badge.color} ${badge.darkColor}`}
          >
            {badge.text}
          </span>
        )}
      </NavLink>
    </li>
  );
};

export default LinkItem;
