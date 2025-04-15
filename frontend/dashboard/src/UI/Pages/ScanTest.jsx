// SecurityPage.js
import React, { useState } from "react";
import { FaCheckCircle, FaBan } from "react-icons/fa";
import DeviceCard from "../DeviceCard";

const SecurityPage = () => {
  const [recognizedDevices, setRecognizedDevices] = useState([]);
  const [newDevices, setNewDevices] = useState([
    {
      id: 1,
      hostname: "Unknown Device 1",
      ip: "192.168.0.23",
      mac: "C4:12:D5:66:AB:FF",
      icon: "FaMobileAlt",
    },
    {
      id: 2,
      hostname: "Unknown Device 2",
      ip: "192.168.0.45",
      mac: "2F:11:AA:FF:89:33",
      icon: "FaLaptop",
    },
  ]);

  const [blockedDevices, setBlockedDevices] = useState([
    {
      id: 3,
      hostname: "Tablet - Guest",
      ip: "192.168.0.77",
      mac: "44:55:66:77:88:99",
      icon: "FaTv",
    },
  ]);

  const [wifiPassword, setWifiPassword] = useState("");
  const [passwordStrength, setPasswordStrength] = useState("");

  const handleRecognize = (deviceId) => {
    const device = newDevices.find((d) => d.id === deviceId);
    setRecognizedDevices([...recognizedDevices, device]);
    setNewDevices(newDevices.filter((d) => d.id !== deviceId));
  };

  const handleUnblock = (deviceId) => {
    setBlockedDevices(blockedDevices.filter((d) => d.id !== deviceId));
  };

  const checkPasswordStrength = (password) => {
    if (password.length < 6) return "Weak";
    if (password.match(/[A-Z]/) && password.match(/[0-9]/)) return "Strong";
    return "Medium";
  };

  const handlePasswordChange = (e) => {
    const newPass = e.target.value;
    setWifiPassword(newPass);
    setPasswordStrength(checkPasswordStrength(newPass));
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-12">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-6">
        Network Security Center
      </h1>

      {/* 1. Device Security Overview */}
      <section>
        <h2 className="text-xl font-semibold mb-4">New Devices</h2>
        {newDevices.length === 0 ? (
          <p className="text-gray-600 dark:text-gray-300">
            No new devices detected.
          </p>
        ) : (
          <div className="flex flex-wrap gap-6">
            {newDevices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                singleActionLabel={
                  <>
                    <FaCheckCircle className="inline mr-1" /> Recognize
                  </>
                }
                singleActionClass="bg-green-600 hover:bg-green-700"
                onSingleAction={() => handleRecognize(device.id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* 2. Blocked Devices */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Blocked Devices</h2>
        {blockedDevices.length === 0 ? (
          <p className="text-gray-600 dark:text-gray-300">
            No devices are currently blocked.
          </p>
        ) : (
          <div className="flex flex-wrap gap-6">
            {blockedDevices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                singleActionLabel={
                  <>
                    <FaBan className="inline mr-1" /> Unblock
                  </>
                }
                singleActionClass="bg-red-600 hover:bg-red-700"
                onSingleAction={() => handleUnblock(device.id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* 3. General Security Settings */}
      <section>
        <h2 className="text-xl font-semibold mb-4">
          Recommended Security Settings
        </h2>
        <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300 list-disc pl-5">
          <li>Use WPA3 encryption (or at least WPA2)</li>
          <li>Hide SSID from public view</li>
          <li>Change your Wi-Fi password regularly</li>
          <li>Enable your router's firewall</li>
        </ul>
      </section>

      {/* 4. Wi-Fi Password Management */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Change Wi-Fi Password</h2>
        <input
          type="password"
          value={wifiPassword}
          onChange={handlePasswordChange}
          placeholder="Enter new Wi-Fi password"
          className="w-full max-w-md p-2 border rounded bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-blue-500"
        />
        {wifiPassword && (
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
            Strength:{" "}
            <span
              className={
                passwordStrength === "Strong"
                  ? "text-green-600"
                  : passwordStrength === "Medium"
                  ? "text-yellow-600"
                  : "text-red-600"
              }
            >
              {passwordStrength}
            </span>
          </p>
        )}
      </section>
    </div>
  );
};

export default SecurityPage;
