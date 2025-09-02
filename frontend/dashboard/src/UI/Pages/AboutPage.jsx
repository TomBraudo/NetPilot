import React from "react";
import { GiRadarSweep } from "react-icons/gi";
import { MdSecurity, MdSpeed, MdDevices, MdAnalytics } from "react-icons/md";
import { FaNetworkWired, FaWifi, FaCloud } from "react-icons/fa";

export default function AboutPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto bg-gray-100 dark:bg-gray-900 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section with Glass Effect */}
        <div className="backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-3xl shadow-2xl border border-gray-200/50 dark:border-white/20 p-8 mb-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-2xl mb-6 shadow-lg shadow-cyan-500/25 dark:shadow-cyan-500/40">
              <FaNetworkWired className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
              About NetPilot
            </h1>
            <div className="w-24 h-1 bg-gradient-to-r from-cyan-400 to-purple-500 mx-auto rounded-full"></div>
          </div>
          
          <div className="space-y-12">
            {/* Introduction Section */}
            <section className="text-center">
              <div className="backdrop-blur-sm bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-2xl p-8 border border-gray-200/30 dark:border-white/10">
                <p className="leading-relaxed text-xl text-gray-800 dark:text-white/90 font-light">
                  NetPilot is an innovative cloud-based platform that gives users full control over their Wi-Fi networks through OpenWrt-compatible routers.
                  <span className="block mt-4 text-cyan-600 dark:text-cyan-300 font-medium">
                    Monitor connected devices, block unwanted users, limit bandwidth, and apply parental controls—all from an intuitive web interface that requires no technical expertise.
                  </span>
                  <span className="block mt-4 text-purple-600 dark:text-purple-300">
                    Access and manage your network from anywhere in the world with maximum control even from afar.
                  </span>
                </p>
              </div>
            </section>

            {/* Main Features Section */}
            <section>
              <div className="text-center mb-12">
                <div className="inline-flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/25 dark:shadow-cyan-500/40">
                    <FaNetworkWired className="w-6 h-6 text-white" />
                  </div>
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    Main Features
                  </h2>
                </div>
                <p className="text-gray-600 dark:text-white/70 text-lg">Advanced network management capabilities at your fingertips</p>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Device Scanning Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-blue-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25 dark:shadow-blue-500/40 group-hover:shadow-blue-500/40 transition-all duration-300">
                        <GiRadarSweep className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-cyan-600 dark:group-hover:text-cyan-300 transition-colors duration-300">
                        Device Scanning
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Comprehensive device scanning capabilities including real-time detection and blocking of unwanted devices.
                      Monitor all connected devices with detailed information and take immediate action to secure your network.
                    </p>
                  </div>
                </div>

                {/* Network Dashboard Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-green-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/25 dark:shadow-green-500/40 group-hover:shadow-green-500/40 transition-all duration-300">
                        <MdAnalytics className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors duration-300">
                        Network Dashboard
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Comprehensive network dashboard displaying real-time bandwidth usage, download and upload speeds.
                      Monitor your network performance at a glance with detailed analytics and usage trends.
                    </p>
                  </div>
                </div>

                {/* Devices Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-purple-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25 dark:shadow-purple-500/40 group-hover:shadow-purple-500/40 transition-all duration-300">
                        <MdDevices className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors duration-300">
                        Devices
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Complete device management with access to all devices in your Wi-Fi history. Map devices to groups
                      and apply timed rules for flexible control over network access and usage patterns.
                    </p>
                  </div>
                </div>

                {/* Bandwidth Control Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-orange-500/20 to-red-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-orange-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/25 dark:shadow-orange-500/40 group-hover:shadow-orange-500/40 transition-all duration-300">
                        <MdSpeed className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-orange-600 dark:group-hover:text-orange-300 transition-colors duration-300">
                        Bandwidth Control
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Apply bandwidth limits on selected groups to ensure fair usage and optimal network performance.
                      Control data consumption and prioritize critical applications with flexible bandwidth allocation.
                    </p>
                  </div>
                </div>

                {/* Content Control Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 to-rose-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-red-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-rose-500 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/25 dark:shadow-red-500/40 group-hover:shadow-red-500/40 transition-all duration-300">
                        <MdSecurity className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-rose-600 dark:group-hover:text-rose-300 transition-colors duration-300">
                        Content Control
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Limit access to unwanted websites and content with comprehensive content filtering capabilities.
                      Protect your network from inappropriate or malicious websites while maintaining productivity.
                    </p>
                  </div>
                </div>

                {/* WiFi Settings Card */}
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-teal-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-6 border border-gray-200/50 dark:border-white/20 hover:border-teal-400/50 transition-all duration-300 hover:scale-105">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-teal-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-teal-500/25 dark:shadow-teal-500/40 group-hover:shadow-teal-500/40 transition-all duration-300">
                        <FaWifi className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-800 dark:text-white group-hover:text-teal-600 dark:group-hover:text-teal-300 transition-colors duration-300">
                        WiFi Settings
                      </h3>
                    </div>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Easily update your WiFi network name and password with a few clicks. Receive email notifications
                      about new unknown devices connecting to your network, keeping you informed about network activity.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Cloud-Powered Control Section */}
            <section>
              <div className="text-center mb-12">
                <div className="inline-flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25 dark:shadow-purple-500/40">
                    <FaCloud className="w-6 h-6 text-white" />
                  </div>
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    Cloud-Powered Control
                  </h2>
                </div>
                <p className="text-gray-600 dark:text-white/70 text-lg max-w-2xl mx-auto">
                  Experience maximum control over your Wi-Fi network from anywhere in the world with our cloud-based platform.
                  Access all your network management tools through any web browser, ensuring you're always connected to your home network.
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-8 border border-gray-200/50 dark:border-white/20 hover:border-purple-400/50 transition-all duration-300 hover:scale-105">
                    <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25 dark:shadow-purple-500/40 mb-6">
                      <MdDevices className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-4 group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors duration-300">
                      Remote Management
                    </h3>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Control your network from work, vacation, or anywhere with internet access. Make changes instantly from your smartphone, tablet, or computer.
                      Your network is always at your fingertips with our seamless cloud infrastructure.
                    </p>
                  </div>
                </div>

                <div className="group relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-500/20 to-purple-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                  <div className="relative backdrop-blur-xl bg-white/80 dark:bg-white/10 rounded-2xl p-8 border border-gray-200/50 dark:border-white/20 hover:border-pink-400/50 transition-all duration-300 hover:scale-105">
                    <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg shadow-pink-500/25 dark:shadow-pink-500/40 mb-6">
                      <MdSecurity className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-4 group-hover:text-pink-600 dark:group-hover:text-pink-300 transition-colors duration-300">
                      24/7 Monitoring
                    </h3>
                    <p className="text-gray-600 dark:text-white/80 leading-relaxed">
                      Stay informed with real-time notifications and access your network dashboard anytime, ensuring peace of mind wherever you are.
                      Never miss a beat with our advanced monitoring and alert system.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* About the Founders Section */}
            <section className="text-center">
              <div className="backdrop-blur-xl bg-gradient-to-r from-gray-100/80 to-blue-50/80 dark:from-slate-800/50 dark:to-slate-700/50 rounded-3xl p-8 border border-gray-200/50 dark:border-white/20">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-6">
                  About the Founders
                </h2>
                <div className="max-w-3xl mx-auto">
                  <p className="leading-relaxed text-xl text-gray-800 dark:text-white/90 font-light mb-4">
                    NetPilot was created by
                    <span className="text-cyan-600 dark:text-cyan-300 font-medium"> Dan Toledano</span>,
                    <span className="text-purple-600 dark:text-purple-300 font-medium"> Tom Braudo</span>, and
                    <span className="text-pink-600 dark:text-pink-300 font-medium"> Chen Feraru</span>
                  </p>
                  <p className="text-gray-600 dark:text-white/70 text-lg">
                    —third-year Computer Science students at the Academic College of Tel Aviv-Yaffo.
                    As our final B.Sc. project, we built a solution to make Wi-Fi management simple, accessible, and powerful for everyone.
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}