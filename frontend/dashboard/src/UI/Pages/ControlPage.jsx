import React, { useState } from "react";
import { Trash2, Shield, ShieldOff } from "lucide-react";

const mockDevices = [
  { name: "iPhone 13", mac: "00:1A:2B:3C:4D:5E" },
  { name: "iPad Pro", mac: "00:3C:4D:5E:6F:7G" },
];

const mockBlacklistedDevices = [
  { name: "Unknown Device", mac: "00:2B:3C:4D:5E:6F" },
  { name: "Suspicious Device", mac: "00:4D:5E:6F:7G:8H" },
];

export default function ControlPage() {
  const [speedLimit, setSpeedLimit] = useState(10);
  const [speedLimitActive, setSpeedLimitActive] = useState(true);
  const [devices, setDevices] = useState(mockDevices);
  const [blacklistedDevices, setBlacklistedDevices] = useState(mockBlacklistedDevices);
  const [isWhitelistMode, setIsWhitelistMode] = useState(true);

  // These would be fetched from backend in real app
  const download = 100;
  const upload = 100;
  const activeDevices = 4;
  const whitelisted = devices.length;
  const blacklisted = blacklistedDevices.length;

  const handleApplySpeedLimit = async () => {
    // Call backend endpoint here
    // await fetch("/api/set_speed_limit", { ... });
    setSpeedLimitActive(true);
  };

  const handleDeleteDevice = (mac) => {
    if (isWhitelistMode) {
      setDevices(devices.filter((d) => d.mac !== mac));
      // Call backend to remove from whitelist
    } else {
      setBlacklistedDevices(blacklistedDevices.filter((d) => d.mac !== mac));
      // Call backend to remove from blacklist
    }
  };

  const toggleMode = () => {
    setIsWhitelistMode(!isWhitelistMode);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-6 px-2 sm:px-4 flex flex-col items-center w-full overflow-x-hidden">
      <div className="w-full max-w-3xl flex flex-col md:flex-row gap-4 md:gap-6 mb-6 md:mb-8">
        {/* Network Status */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6 flex flex-col gap-4 min-w-0">
          <h2 className="text-lg font-semibold mb-2 dark:text-white">Network Status</h2>
          <div className="flex flex-wrap gap-2 sm:gap-4 mb-2">
            <StatusBox label="Download" value={download} unit="Mbps" />
            <StatusBox label="Upload" value={upload} unit="Mbps" />
            <StatusBox label="Whitelisted" value={whitelisted} />
            <StatusBox label="Blacklisted" value={blacklisted} />
            <StatusBox label="Active Devices" value={activeDevices} />
          </div>
          {speedLimitActive && (
            <div className="bg-red-50 dark:bg-red-900/40 text-red-600 dark:text-red-300 rounded p-2 text-sm font-medium border border-red-200 dark:border-red-400/30">
              <span>• Speed limits are currently active</span>
            </div>
          )}
        </div>
        {/* Speed Limit Control */}
        <div className="w-full md:w-1/3 bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6 flex flex-col gap-4 min-w-0 mt-4 md:mt-0">
          <h2 className="text-lg font-semibold mb-2 dark:text-white">Speed Limit Control</h2>
          <label className="text-sm mb-1 dark:text-gray-300">Download Speed (Mbps)</label>
          <input
            type="number"
            min={1}
            className="border rounded px-3 py-2 mb-3 bg-white dark:bg-gray-900 dark:text-white dark:border-gray-700 w-full"
            value={speedLimit}
            onChange={(e) => setSpeedLimit(e.target.value)}
          />
          <button
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded py-2 transition w-full"
            onClick={handleApplySpeedLimit}
          >
            Apply Speed Limit
          </button>
        </div>
      </div>

      {/* Mode Toggle Button */}
      <div className="w-full max-w-3xl mb-4">
        <button
          onClick={toggleMode}
          className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-xl shadow px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
        >
          {isWhitelistMode ? (
            <>
              <Shield className="w-5 h-5 text-green-500" />
              <span className="text-gray-700 dark:text-gray-300">Switch to Blacklist Mode</span>
            </>
          ) : (
            <>
              <ShieldOff className="w-5 h-5 text-red-500" />
              <span className="text-gray-700 dark:text-gray-300">Switch to Whitelist Mode</span>
            </>
          )}
        </button>
      </div>

      {/* Device List */}
      <div className="w-full max-w-3xl bg-white dark:bg-gray-800 rounded-xl shadow p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">
          {isWhitelistMode ? "Whitelisted Devices" : "Blacklisted Devices"}
        </h2>
        <div className="flex flex-col gap-3 max-h-80 overflow-y-auto">
          {(isWhitelistMode ? devices : blacklistedDevices).map((device) => (
            <div
              key={device.mac}
              className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-gray-50 dark:bg-gray-900 rounded p-3 gap-2 sm:gap-0"
            >
              <div>
                <div className="font-medium text-gray-900 dark:text-white">{device.name}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{device.mac}</div>
              </div>
              <button
                className="p-2 rounded hover:bg-red-100 dark:hover:bg-red-900/40 self-end sm:self-auto"
                onClick={() => handleDeleteDevice(device.mac)}
                title={`Remove from ${isWhitelistMode ? 'whitelist' : 'blacklist'}`}
              >
                <Trash2 className="w-5 h-5 text-red-500" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatusBox({ label, value, unit }) {
  return (
    <div className="flex flex-col items-center bg-gray-50 dark:bg-gray-900 rounded-lg px-3 py-2 min-w-[80px] flex-1">
      <span className="text-sm text-gray-500 dark:text-gray-300">{label}</span>
      <span className="text-xl font-bold text-gray-800 dark:text-white">
        {value}
        {unit && <span className="text-base font-normal ml-1">{unit}</span>}
      </span>
    </div>
  );
}
