import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Wifi } from "lucide-react";

function ScanButton({ onScan, isScanning }) {
  const [isHovered, setIsHovered] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleClick = () => {
    if (location.pathname === "/scan") {
      if (onScan) onScan();
    } else {
      navigate("/scan", { state: { autoScan: true } });
    }
  };

  useEffect(() => {
    if (isScanning) {
      setIsHovered(false);
    }
  }, [isScanning]);

  if (isScanning) return null;

  return (
    <button
      className={`relative group px-8 py-4 rounded-full font-semibold text-lg transition-all duration-300
        ${
          isScanning
            ? "bg-blue-600 opacity-55 text-white cursor-not-allowed"
            : "bg-blue-500/10 border border-blue-400/30 backdrop-blur-sm text-blue-900 dark:text-white hover:border-blue-400/50 hover:bg-blue-500/20"
        }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
      disabled={isScanning}
    >
      <div className="relative z-10 flex items-center gap-3">
        <span>{isScanning ? "SCANNING..." : "Scan Network"}</span>
        {isScanning ? (
          ""
        ) : (
          <Wifi
            className={`w-5 h-5 transition-transform duration-300 ${
              isHovered ? "scale-110" : "scale-100"
            }`}
          />
        )}
      </div>

      {/* Animated rings only when not scanning */}
      {!isScanning && (
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
      )}
    </button>
  );
}

export default ScanButton;
