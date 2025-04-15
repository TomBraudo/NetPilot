import React from "react";

const Dashboard = () => {
  return <div>Dashboard</div>;
};

<<<<<<< Updated upstream
export default Dashboard;
=======
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
            href="https://youtu.be/7cxiYmn3OTU?si=etGet3mLj7lF3VVN"
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
>>>>>>> Stashed changes
