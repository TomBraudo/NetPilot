import React from "react";
import { GiRadarSweep } from "react-icons/gi";
import { MdSecurity, MdSpeed, MdDevices } from "react-icons/md";
import { FaNetworkWired } from "react-icons/fa";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-8 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">About NetPilot</h1>
          
          <div className="space-y-8 text-gray-600 dark:text-gray-300">
            <section>
              <p className="leading-relaxed text-lg">
                NetPilot is an innovative web-based platform that gives users full control over their Wi-Fi networks through OpenWrt-compatible routers. 
                Monitor connected devices, block unwanted users, limit bandwidth, and apply parental controls—all from an intuitive interface that requires no technical expertise.
              </p>
            </section>

            <section className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <FaNetworkWired className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Main Features</h2>
              </div>
              
              <div className="flex flex-col gap-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <GiRadarSweep className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Device Scanning</h3>
                  </div>
                  <p className="leading-relaxed text-gray-600 dark:text-gray-300">
                    Quickly scan your Wi-Fi network to view all connected devices with detailed information including IP addresses, MAC addresses, and device names. 
                    Get full visibility into network usage and spot unfamiliar devices to keep your network secure.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                      <MdSecurity className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Advanced Device Control</h3>
                  </div>
                  <p className="leading-relaxed text-gray-600 dark:text-gray-300">
                    Manage device access with powerful control tools—block unwanted devices or limit their browsing speed to reduce bandwidth usage. 
                    Group multiple devices together and apply custom rules for flexible network management.
                  </p>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                      <MdSpeed className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Wi-Fi Network Management</h3>
                  </div>
                  <p className="leading-relaxed text-gray-600 dark:text-gray-300">
                    View and manage key Wi-Fi network details including internet provider information and real-time speed tests. 
                    Monitor connection quality and make quick adjustments from a single dashboard.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">About the Founders</h2>
              <p className="leading-relaxed">
                NetPilot was created by Dan Toledano, Tom Braudo, and Chen Feraru—third-year Computer Science students at the Academic College of Tel Aviv-Yaffo. 
                As our final B.Sc. project, we built a solution to make Wi-Fi management simple, accessible, and powerful for everyone.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}