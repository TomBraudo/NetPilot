import React from "react";

const Main = ({ children }) => {
  return (
    <div
      className="text-gray-500 bg-gray-100 p-4 flex flex-wrap gap-6 transition-all duration-300 pt-16 dark:bg-gray-800 min-h-screen 
      w-full lg:ml-64"
    >
      {children}
    </div>
  );
};

export default Main;
