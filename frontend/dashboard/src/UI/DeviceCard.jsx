import React from "react";
import {
  FaHandPaper,
  FaTachometerAlt,
  FaMobileAlt,
  FaLaptop,
  FaTv,
  FaWifi,
  FaRegQuestionCircle,
} from "react-icons/fa";

const iconMap = {
  FaMobileAlt: FaMobileAlt,
  FaLaptop: FaLaptop,
  FaTv: FaTv,
  FaWifi: FaWifi,
};

const DeviceCard = ({ device }) => {
  const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;

  return (
    <div className="bg-white dark:bg-gray-700 shadow-lg rounded-2xl p-5 flex flex-col items-center gap-3 w-72">
      <div className="text-5xl text-blue-500">
        <IconComponent />
      </div>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
        {device.hostname}
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        IP: {device.ip}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-300">
        MAC: {device.mac}
      </p>

      <div className="flex gap-4 mt-3">
        <button className="bg-red-500 text-white p-2 rounded-full shadow-md hover:bg-red-600 transition">
          <FaHandPaper size={20} />
        </button>
        <button className="bg-yellow-400 text-white p-2 rounded-full shadow-md hover:bg-yellow-500 transition">
          <FaTachometerAlt size={20} />
        </button>
      </div>
    </div>
  );
};

export default DeviceCard;
