// import React, { useState, useEffect, useRef } from "react";
// import DeviceCard from "../DeviceCard";
// import ScannerAnimation from "../../components/ScannerAnimation";

// const iconMap = {
//   router: "BsRouter",
//   laptop: "FaLaptop",
//   mobile: "FaMobileAlt",
//   tv: "FaTv",
// };

// const identifyDeviceType = (hostname, ip) => {
//   if (hostname.toLowerCase().includes("router") || ip.endsWith(".1"))
//     return "router";
//   if (hostname.toLowerCase().includes("laptop")) return "laptop";
//   if (
//     hostname.toLowerCase().includes("iphone") ||
//     hostname.toLowerCase().includes("mobile")
//   )
//     return "mobile";
//   if (hostname.toLowerCase().includes("tv")) return "tv";
//   return "unknown";
// };

// const formatDevices = (data) => {
//   return data.map(({ hostname, ip, mac }) => {
//     const type = identifyDeviceType(hostname, ip);
//     return {
//       type,
//       hostname: hostname !== "Unknown" ? hostname : "Unnamed Device",
//       ip,
//       mac,
//       icon: iconMap[type] || "FaRegQuestionCircle",
//     };
//   });
// };

// const getFormattedDate = () => {
//   const now = new Date();
//   const day = now.getDate().toString().padStart(2, "0");
//   const month = (now.getMonth() + 1).toString().padStart(2, "0");
//   const year = now.getFullYear();
//   const hours = now.getHours().toString().padStart(2, "0");
//   const minutes = now.getMinutes().toString().padStart(2, "0");

//   return `${day}/${month}/${year}, ${hours}:${minutes}`;
// };

// const ScanPage = () => {
//   const [devices, setDevices] = useState(() => {
//     const savedDevices = localStorage.getItem("scannedDevices");
//     return savedDevices ? JSON.parse(savedDevices) : [];
//   });

//   const [error, setError] = useState(null);
//   const [isScanning, setIsScanning] = useState(false);
//   const [lastScanTime, setLastScanTime] = useState(() => {
//     return localStorage.getItem("lastScanTime") || null;
//   });

//   const isMounted = useRef(true);

//   useEffect(() => {
//     isMounted.current = true;
//     return () => {
//       isMounted.current = false;
//     };
//   }, []);

//   useEffect(() => {
//     localStorage.setItem("scannedDevices", JSON.stringify(devices));
//   }, [devices]);

//   const handleNetworkScan = async () => {
//     setIsScanning(true);
//     setError(null);

//     try {
//       const res = await fetch("http://localhost:5000/api/network_scan");

//       console.log("Response received:", res);

//       if (!res.ok) {
//         throw new Error(`HTTP error! Status: ${res.status}`);
//       }

//       const data = await res.json();
//       console.log("Parsed JSON data:", data);

//       if (isMounted.current) {
//         const formattedDevices = formatDevices(data['data']);
//         console.log("Formatted devices:", formattedDevices);
//         setDevices(formattedDevices);

//         const scanTime = getFormattedDate();
//         setLastScanTime(scanTime);
//         localStorage.setItem("lastScanTime", scanTime);
//       }
//     } catch (err) {
//       console.error("Fetch error:", err);
//       if (isMounted.current) {
//         setError(`Error: ${err.message}`);
//       }
//     } finally {
//       if (isMounted.current) {
//         console.log("Scan finished, updating isScanning to false");
//         setIsScanning(false);
//       }
//     }
//   };

//   return (
//     <div className="p-5 flex flex-col items-center min-h-screen">
//       <button
//         onClick={handleNetworkScan}
//         disabled={isScanning}
//         className={`w-40 h-10 flex items-center justify-center ${
//           isScanning ? "bg-gray-400" : "bg-blue-500 hover:bg-blue-600"
//         } text-white p-2 rounded-md transition mb-6`}
//       >
//         {isScanning ? "SCANNING..." : "Scan Network"}
//       </button>
//       {isScanning && (
//         <div className="p-5">
//           <ScannerAnimation />
//         </div>
//       )}
//       {error && <p className="text-red-600 mt-4">{error}</p>}
//       {!isScanning && lastScanTime && (
//         <p className="text-gray-500 mt-4 text-lg font-medium">
//           Last scan: {lastScanTime}
//         </p>
//       )}
//       {!isScanning && (
//         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 w-full">
//           {devices.map((device, index) => (
//             <DeviceCard key={index} device={device} />
//           ))}
//         </div>
//       )}
//     </div>
//   );
// };
// export default ScanPage;

import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import DeviceCard from "../DeviceCard";
import ScannerAnimation from "../../components/ScannerAnimation";

const iconMap = {
  router: "BsRouter",
  laptop: "FaLaptop",
  mobile: "FaMobileAlt",
  tv: "FaTv",
};

const identifyDeviceType = (hostname, ip) => {
  if (hostname.toLowerCase().includes("router") || ip.endsWith(".1"))
    return "router";
  if (hostname.toLowerCase().includes("laptop")) return "laptop";
  if (
    hostname.toLowerCase().includes("iphone") ||
    hostname.toLowerCase().includes("mobile")
  )
    return "mobile";
  if (hostname.toLowerCase().includes("tv")) return "tv";
  return "unknown";
};

const formatDevices = (data) => {
  return data.map(({ hostname, ip, mac }) => {
    const type = identifyDeviceType(hostname, ip);
    return {
      type,
      hostname: hostname !== "Unknown" ? hostname : "Unnamed Device",
      ip,
      mac,
      icon: iconMap[type] || "FaRegQuestionCircle",
    };
  });
};

const getFormattedDate = () => {
  const now = new Date();
  const day = now.getDate().toString().padStart(2, "0");
  const month = (now.getMonth() + 1).toString().padStart(2, "0");
  const year = now.getFullYear();
  const hours = now.getHours().toString().padStart(2, "0");
  const minutes = now.getMinutes().toString().padStart(2, "0");

  return `${day}/${month}/${year}, ${hours}:${minutes}`;
};

const ScanPage = () => {
  const [devices, setDevices] = useState(() => {
    const savedDevices = localStorage.getItem("scannedDevices");
    return savedDevices ? JSON.parse(savedDevices) : [];
  });

  const [error, setError] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(() => {
    return localStorage.getItem("lastScanTime") || null;
  });

  const isMounted = useRef(true);
  const hasAutoScanned = useRef(false);
  const location = useLocation();

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    localStorage.setItem("scannedDevices", JSON.stringify(devices));
  }, [devices]);

  useEffect(() => {
    if (location.state?.autoScan && !hasAutoScanned.current) {
      hasAutoScanned.current = true;
      handleNetworkScan();
    }
  }, [location.state]);

  const handleNetworkScan = async () => {
    setIsScanning(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:5000/api/router_scan");

      if (!res.ok) {
        throw new Error(`HTTP error! Status: ${res.status}`);
      }

      const data = await res.json();

      if (isMounted.current) {
        const formattedDevices = formatDevices(data["data"]);

        setDevices(formattedDevices);

        const scanTime = getFormattedDate();
        setLastScanTime(scanTime);
        localStorage.setItem("lastScanTime", scanTime);
      }
    } catch (err) {
      if (isMounted.current) {
        setError(`Error: ${err.message}`);
      }
    } finally {
      if (isMounted.current) {
        setIsScanning(false);
      }
    }
  };

  return (
    <div className="p-5 flex flex-col items-center min-h-screen">
      <button
        onClick={handleNetworkScan}
        disabled={isScanning}
        className={`w-40 h-10 flex items-center justify-center ${
          isScanning ? "bg-gray-400" : "bg-blue-500 hover:bg-blue-600"
        } text-white p-2 rounded-md transition mb-6`}
      >
        {isScanning ? "SCANNING..." : "Scan Network"}
      </button>

      {/* 👇 האנימציה שלך חוזרת לכאן בגאווה */}
      {isScanning && (
        <div className="p-5">
          <ScannerAnimation />
        </div>
      )}

      {error && <p className="text-red-600 mt-4">{error}</p>}

      {!isScanning && lastScanTime && (
        <p className="text-gray-500 mt-4 text-lg font-medium">
          Last scan: {lastScanTime}
        </p>
      )}

      {!isScanning && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-5 w-full">
          {devices.map((device, index) => (
            <DeviceCard key={index} device={device} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ScanPage;
