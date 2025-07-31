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
                NetPilot is an innovative web-based platform designed to give users full control over their home or office Wi-Fi networks. 
                By leveraging the power of OpenWrt on compatible routers, NetPilot provides a simple and intuitive interface for managing connected devices. 
                Whether you're looking to monitor who's connected, block unwanted users, limit bandwidth usage, or apply parental control settings, 
                NetPilot puts these tools at your fingertips. Our goal is to make network management accessible, efficient, and secure for everyone—no technical expertise required.
              </p>
            </section>

            <section className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <FaNetworkWired className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Main Features</h2>
              </div>
              
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <GiRadarSweep className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-white">Device Scanning</h3>
                  </div>
                  <p className="leading-relaxed text-gray-600 dark:text-gray-300">
                    NetPilot allows you to quickly scan your Wi-Fi network and view all currently connected devices. With just a few clicks, 
                    you can see detailed information such as IP addresses, MAC addresses, and device names (when available). This feature gives 
                    you full visibility into who's using your network at any given time—helping you spot unfamiliar devices, monitor usage, 
                    and keep your network secure.
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
                    NetPilot gives you powerful tools to manage how each device interacts with your Wi-Fi network. You can easily block unwanted 
                    devices from accessing the internet or limit their browsing speed to reduce bandwidth usage. For even more flexibility, 
                    NetPilot lets you group multiple devices—such as all your kids' phones and tablets—and apply custom rules to them.
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
                    With NetPilot, you can easily view and manage key details of your Wi-Fi network. See information about your internet provider, 
                    perform real-time speed tests to check your connection quality, and make quick adjustments—all from a single dashboard.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">About the Founders</h2>
              <p className="leading-relaxed">
                NetPilot was created by Dan Toledano, Tom Braudo, and Chen Feraru— third-year Computer Science students at the Academic College of 
                Tel Aviv-Yaffo. As part of our final B.Sc. project, we set out to build a solution to a problem we all face daily: managing our 
                Wi-Fi networks. We realized that despite how central Wi-Fi is to modern life, most people don't have an easy way to see who's 
                connected to their network or control how it's used. That's why we developed NetPilot—to make Wi-Fi management simple, accessible, 
                and powerful for everyone.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}