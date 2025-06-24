import { Wifi, ArrowRight } from "lucide-react";
import NetworkBackground from "../../components/NetworkBackground";
import ScanButton from "../../components/ScanButton";

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
