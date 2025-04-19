// FaqsPage.js
import React, { useState } from "react";
import { ChevronDown, ChevronUp, Search } from "lucide-react";

const FaqsPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [activeCategory, setActiveCategory] = useState("all");

  const faqData = [
    {
      id: 1,
      category: "network",
      question:
        "Why is my internet connection slower than what I'm paying for?",
      answer:
        "Several factors can affect your internet speed: network congestion, Wi-Fi interference, outdated hardware, or distance from the router. Try running a speed test at different times, use a wired connection for comparison, and ensure your router firmware is up to date.",
    },
    {
      id: 2,
      category: "security",
      question: "How can I secure my home network from unauthorized access?",
      answer:
        "1. Use WPA3 encryption if available, or at minimum WPA2\n2. Change default router passwords\n3. Enable firewall protection\n4. Regularly update router firmware\n5. Create a guest network for visitors\n6. Use strong, unique passwords",
    },
    {
      id: 3,
      category: "devices",
      question: "What does it mean when a device is 'blocked' on my network?",
      answer:
        "When you block a device, it can no longer access your network or internet connection through your router. The device might still see your network name (SSID) but won't be able to connect, even with the correct password.",
    },
    {
      id: 4,
      category: "network",
      question: "How do bandwidth limits work?",
      answer:
        "Bandwidth limits restrict how much data a device can transfer per second. For example, setting a 10Mbps limit means the device can't exceed that speed, even if your network is capable of faster speeds. This is useful for preventing single devices from monopolizing your connection.",
    },
    {
      id: 5,
      category: "security",
      question: "What is MAC address filtering?",
      answer:
        "MAC address filtering is a security feature that allows or blocks devices based on their unique hardware address (MAC address). While it adds a layer of security, it shouldn't be your only security measure as MAC addresses can be spoofed.",
    },
    {
      id: 6,
      category: "devices",
      question: "Why do some devices show as 'Unknown' in the device list?",
      answer:
        "Devices may appear as 'Unknown' if they haven't shared their hostname with the router, or if they're using privacy features that mask their identity. This is common with some IoT devices and devices using MAC address randomization.",
    },
    {
      id: 7,
      category: "network",
      question: "What's the difference between 2.4GHz and 5GHz Wi-Fi?",
      answer:
        "2.4GHz offers better range but slower speeds and more interference from other devices. 5GHz provides faster speeds and less interference but shorter range. 2.4GHz is better for devices far from the router, while 5GHz is ideal for high-bandwidth activities like streaming.",
    },
    {
      id: 8,
      category: "security",
      question: "Should I hide my network SSID?",
      answer:
        "Hiding your SSID (network name) provides minimal security benefit and can make it harder to connect legitimate devices. Instead, focus on strong passwords, encryption, and regular security updates. Hidden networks can still be discovered by determined attackers.",
    },
    {
      id: 9,
      category: "network",
      question: "What does “scanning the network” mean?",
      answer:
        "Scanning the network means checking which devices are currently connected to your Wi-Fi. NetPilot uses your router to list these devices by IP address, MAC address, and (when available) device name.",
    },
    {
      id: 10,
      category: "network",
      question: "Will scanning slow down my internet?",
      answer:
        "Not at all. Scanning is a lightweight process that only queries your router for information—it doesn’t interfere with your internet speed.",
    },
    {
      id: 11,
      category: "devices",
      question: "Can NetPilot see devices connected through both Wi-Fi and Ethernet?",
      answer:
        "Yes! As long as the device is connected to your router (via Wi-Fi or cable), NetPilot can detect it during the scan.",
    },
    {
      id: 12,
      category: "devices",
      question: "What's the difference between blocking a device and limiting it?",
      answer:
        "Blocking completely cuts the device off from your Wi-Fi. Limiting lets the device stay connected but slows down its internet speed, which can help prioritize more important devices.",
    },
    {
      id: 13,
      category: "network",
      question: "How often should I scan my network?",
      answer:
        "You can scan anytime you want, but it's a good habit to scan regularly—especially if you notice slow speeds or suspect someone is using your Wi-Fi without permission.",
    },
    {
      id: 14,
      category: "devices",
      question: "What are device groups used for?",
      answer:
        "Device groups help you manage multiple devices together—for example, putting all your kids' devices in a “Kids” group so you can apply the same rules (like bedtime restrictions) to all of them at once.",
    },
    {
      id: 15,
      category: "security",
      question: "Is it safe to use NetPilot on my home network?",
      answer:
        "Yes, NetPilot only interacts with your router via OpenWrt's secure interface. It doesn't send your data to external servers and keeps your control fully local and private.",
    },
  ];

  const categories = ["all", "network", "security", "devices"];

  const filteredFAQs = faqData.filter(
    (faq) =>
      (activeCategory === "all" || faq.category === activeCategory) &&
      (faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
        Frequently Asked Questions
      </h1>

      {/* Search and Filter Section */}
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="Search FAQs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeCategory === category
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* FAQ List */}
      <div className="space-y-3 flex flex-col items-center">
        {filteredFAQs.map((faq) => (
          <div
            key={faq.id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-md"
            style={{ minHeight: "80px", width: "100%", maxWidth: "550px" }}
          >
            <button
              onClick={() =>
                setExpandedId(expandedId === faq.id ? null : faq.id)
              }
              className="w-full px-4 py-3 flex items-center justify-between text-left"
            >
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {faq.question}
              </span>
              {expandedId === faq.id ? (
                <ChevronUp className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              )}
            </button>

            <div
              className={`transition-all duration-300 ease-in-out overflow-hidden ${
                expandedId === faq.id
                  ? "max-h-96 opacity-100"
                  : "max-h-0 opacity-0"
              } px-4 pb-3`}
            >
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line">
                  {faq.answer}
                </p>
              </div>
            </div>
          </div>
        ))}

        {filteredFAQs.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No FAQs found matching your search criteria
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FaqsPage;
