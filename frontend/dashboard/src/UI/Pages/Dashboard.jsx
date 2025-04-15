import React, { useState } from "react";
import { Wifi, ArrowRight } from "lucide-react";
import NetworkBackground from "../../components/NetworkBackground";
import { useNavigate } from "react-router-dom";

function ScanButton() {
  const [isHovered, setIsHovered] = useState(false);
  const navigate = useNavigate();
  return (
    <button
      className="relative group bg-blue-500/10 backdrop-blur-sm border border-blue-400/30 text-blue-900 dark:text-white px-8 py-4 rounded-full font-semibold text-lg transition-all duration-300 hover:border-blue-400/50 hover:bg-blue-500/20"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => navigate("/scan", { state: { autoScan: true } })}
    >
      <div className="relative z-10 flex items-center gap-3">
        <span>Scan Network</span>
        <Wifi
          className={`w-5 h-5 transition-transform duration-300 ${
            isHovered ? "scale-110" : "scale-100"
          }`}
        />
      </div>

      {/* Animated rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className={`absolute w-full h-full rounded-full transition-opacity duration-300 ${
            isHovered ? "opacity-100" : "opacity-0"
          }`}
        >
          <div className="absolute inset-0 rounded-full border border-blue-400/30 animate-ping" />
          <div
            className="absolute inset-0 rounded-full border border-blue-400/20 animate-ping"
            style={{ animationDelay: "0.2s" }}
          />
          <div
            className="absolute inset-0 rounded-full border border-blue-400/10 animate-ping"
            style={{ animationDelay: "0.4s" }}
          />
        </div>
      </div>
    </button>
  );
}

function App() {
  return (
    <div className="relative text-gray-500 bg-gray-100 dark:bg-gray-800 w-full h-screen overflow-hidden flex items-center justify-center">
      <NetworkBackground />

      <main className="max-w-2xl text-center relative z-10 px-4">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 text-gray-900 dark:text-white">
          Who's using your Wi-Fi?
        </h1>

        <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 max-w-xl mx-auto">
          NetPilot lets you see, control, and manage every connected device
        </p>

        <div className="flex justify-center mb-12">
          <ScanButton />
        </div>

        <div className="text-gray-400 dark:text-gray-300">
          <p className="mb-2">
            Note: NetPilot requires OpenWrt installed on your router.
          </p>
          <a
            href="https://www.youtube.com/watch?v=7cxiYmn3OTU"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-500 hover:text-blue-400 transition-colors group"
          >
            <span className="group-hover:underline">
              👉 Click here for a setup guide
            </span>
            <ArrowRight className="w-4 h-4 ml-1 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </a>
        </div>
      </main>
    </div>
  );
}

export default App;
