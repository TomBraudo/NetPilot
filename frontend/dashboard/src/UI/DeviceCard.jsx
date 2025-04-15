// import React from "react";
// import {
//   FaHandPaper,
//   FaTachometerAlt,
//   FaMobileAlt,
//   FaLaptop,
//   FaTv,
//   FaWifi,
//   FaRegQuestionCircle,
// } from "react-icons/fa";
// import { BsRouter } from "react-icons/bs";
// const iconMap = {
//   FaMobileAlt: FaMobileAlt,
//   FaLaptop: FaLaptop,
//   FaTv: FaTv,
//   FaWifi: FaWifi,
//   BsRouter: BsRouter,
// };

// const DeviceCard = ({ device }) => {
//   const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;

//   return (
//     <div className="bg-white dark:bg-gray-700 shadow-lg rounded-2xl p-5 flex flex-col items-center gap-3 w-72">
//       <div className="text-5xl text-blue-500">
//         <IconComponent />
//       </div>

//       <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
//         {device.hostname}
//       </h3>
//       <p className="text-sm text-gray-600 dark:text-gray-300">
//         IP: {device.ip}
//       </p>
//       <p className="text-sm text-gray-600 dark:text-gray-300">
//         MAC: {device.mac}
//       </p>

//       <div className="flex gap-4 mt-3">
//         <button className="bg-red-500 text-white p-2 rounded-full shadow-md hover:bg-red-600 transition">
//           <FaHandPaper size={20} />
//         </button>
//         <button className="bg-yellow-400 text-white p-2 rounded-full shadow-md hover:bg-yellow-500 transition">
//           <FaTachometerAlt size={20} />
//         </button>
//       </div>
//     </div>
//   );
// };

// export default DeviceCard;

import React, { useState } from "react";
import {
  FaHandPaper,
  FaTachometerAlt,
  FaMobileAlt,
  FaLaptop,
  FaTv,
  FaWifi,
  FaRegQuestionCircle,
} from "react-icons/fa";
import { BsRouter } from "react-icons/bs";

const iconMap = {
  FaMobileAlt: FaMobileAlt,
  FaLaptop: FaLaptop,
  FaTv: FaTv,
  FaWifi: FaWifi,
  BsRouter: BsRouter,
};

const DeviceCard = ({
  device,
  singleActionLabel,
  singleActionClass = "",
  onSingleAction,
}) => {
  const IconComponent = iconMap[device.icon] || FaRegQuestionCircle;

  const [showBlockModal, setShowBlockModal] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [limitValue, setLimitValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  const handleBlockConfirm = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/block", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: device.ip }),
      });

      if (!res.ok) throw new Error("Failed to block device");

      setActionMessage("Device successfully blocked.");
    } catch (err) {
      setActionMessage("Failed to block device.");
      console.error(err);
    } finally {
      setLoading(false);
      setShowBlockModal(false);
    }
  };

  const handleLimitConfirm = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/api/limit_bandwidth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: device.ip, limit: limitValue }),
      });

      if (!res.ok) throw new Error("Failed to limit bandwidth");

      setActionMessage(`Bandwidth limited to ${limitValue} Mbps.`);
    } catch (err) {
      setActionMessage("Failed to limit bandwidth.");
      console.error(err);
    } finally {
      setLoading(false);
      setShowLimitModal(false);
      setLimitValue("");
    }
  };

  return (
    <>
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
          <button
            onClick={() => setShowBlockModal(true)}
            className="bg-red-500 text-white p-2 rounded-full shadow-md hover:bg-red-600 transition"
          >
            <FaHandPaper size={20} />
          </button>
          <button
            onClick={() => setShowLimitModal(true)}
            className="bg-yellow-400 text-white p-2 rounded-full shadow-md hover:bg-yellow-500 transition"
          >
            <FaTachometerAlt size={20} />
          </button>
        </div>

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

      {/* Block Modal */}
      {showBlockModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg w-96 text-center">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Are you sure you want to block this device?
            </h2>
            <div className="flex justify-center gap-4 mt-6">
              <button
                onClick={handleBlockConfirm}
                disabled={loading}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md"
              >
                {loading ? "Blocking..." : "Block"}
              </button>
              <button
                onClick={() => setShowBlockModal(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 dark:bg-gray-600 dark:text-white px-4 py-2 rounded-md"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

<<<<<<< Updated upstream
      <div className="flex gap-4 mt-3">
        {singleActionLabel && onSingleAction ? (
          <button
            onClick={onSingleAction}
            className={`text-white px-4 py-1.5 rounded-full shadow-md transition text-sm ${singleActionClass}`}
          >
            {singleActionLabel}
          </button>
        ) : (
          <>
            <button className="bg-red-500 text-white p-2 rounded-full shadow-md hover:bg-red-600 transition">
              <FaHandPaper size={20} />
            </button>
            <button className="bg-yellow-400 text-white p-2 rounded-full shadow-md hover:bg-yellow-500 transition">
              <FaTachometerAlt size={20} />
            </button>
          </>
        )}
      </div>
    </div>
=======
      {/* Limit Modal */}
      {showLimitModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg w-96">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Limit the bandwidth of this device to:
            </h2>
            <input
              type="number"
              placeholder="Mbps"
              value={limitValue}
              onChange={(e) => setLimitValue(e.target.value)}
              className="w-full p-2 mb-4 rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            />
            <div className="flex justify-center gap-4">
              <button
                onClick={handleLimitConfirm}
                disabled={loading}
                className="bg-yellow-400 hover:bg-yellow-500 text-white px-4 py-2 rounded-md"
              >
                {loading ? "Applying..." : "Apply Limit"}
              </button>
              <button
                onClick={() => {
                  setShowLimitModal(false);
                  setLimitValue("");
                }}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 dark:bg-gray-600 dark:text-white px-4 py-2 rounded-md"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
>>>>>>> Stashed changes
  );
};

export default DeviceCard;
