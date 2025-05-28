import React, { useState } from "react";
import {
  FaHandPaper,
  FaTachometerAlt,
  FaMobileAlt,
  FaLaptop,
  FaTv,
  FaWifi,
  FaRegQuestionCircle,
  FaShieldAlt,
  FaBan,
  FaCheck,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";

const iconMap = {
  FaMobileAlt: FaMobileAlt,
  FaLaptop: FaLaptop,
  FaTv: FaTv,
  FaWifi: FaWifi,
  BsRouter: BsRouter,
};

const DeviceCard = ({ device }) => {
  const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [limitValue, setLimitValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  const handleAction = async (action) => {
    setLoading(true);
    try {
      const endpoint = {
        whitelist: "http://localhost:5000/whitelist",
        blacklist: "http://localhost:5000/blacklist",
        block: "http://localhost:5000/api/block"
      }[action];

      const body = action === 'whitelist' 
        ? { ip: device.ip, name: device.hostname, description: `${device.hostname} - ${device.mac}` }
        : { ip: device.ip, mac: device.mac };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`Failed to ${action} device`);

      const result = await res.json();
      if (result.success) {
        setActionMessage(`Device successfully ${action}ed.`);
        // Update localStorage to trigger control page refresh
        if (action === 'whitelist') {
          const event = new StorageEvent('storage', {
            key: 'whitelistUpdate',
            newValue: Date.now().toString()
          });
          window.dispatchEvent(event);
        }
      } else {
        throw new Error(result.message || `Failed to ${action} device`);
      }
    } catch (err) {
      setActionMessage(`Failed to ${action} device: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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

      {/* Action Buttons */}
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => handleAction('whitelist')}
          disabled={loading}
          className="bg-green-500 text-white p-2 rounded-full shadow-md hover:bg-green-600 transition flex items-center gap-1"
          title="Add to Whitelist"
        >
          <FaCheck size={16} />
          <span className="text-xs">Whitelist</span>
        </button>
        <button
          onClick={() => handleAction('blacklist')}
          disabled={loading}
          className="bg-yellow-500 text-white p-2 rounded-full shadow-md hover:bg-yellow-600 transition flex items-center gap-1"
          title="Add to Blacklist"
        >
          <FaShieldAlt size={16} />
          <span className="text-xs">Blacklist</span>
        </button>
        <button
          onClick={() => handleAction('block')}
          disabled={loading}
          className="bg-red-500 text-white p-2 rounded-full shadow-md hover:bg-red-600 transition flex items-center gap-1"
          title="Block Device"
        >
          <FaBan size={16} />
          <span className="text-xs">Block</span>
        </button>
      </div>

      {/* Status message */}
      {actionMessage && (
        <p
          className={`text-sm text-center mt-2 ${
            /error|fail|failed/i.test(actionMessage)
              ? "text-red-500 dark:text-red-400"
              : "text-green-500 dark:text-green-400"
          }`}
        >
          {actionMessage}
        </p>
      )}
    </div>
  );
};

export default DeviceCard;
