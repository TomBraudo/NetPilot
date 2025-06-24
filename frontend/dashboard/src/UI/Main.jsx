import React from "react";

const Main = ({ children }) => {
  return (
    <div
      className="text-gray-500 bg-gray-100 p-4 flex flex-wrap justify-center gap-6 transition-all duration-300 pt-16 dark:bg-gray-800 min-h-screen 
      w-full"
    >
      {children}
    </div>
  );
};

export default Main;
