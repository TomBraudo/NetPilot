import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Wifi } from "lucide-react";
import { useAuth } from "../context/AuthContext";

function ScanButton({ onScan, isScanning }) {
  const [isHovered, setIsHovered] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionStarted } = useAuth();

  const handleClick = () => {
    if (!sessionStarted) return;
    if (location.pathname === "/scan") {
      if (onScan) onScan();
    } else {
      navigate("/scan");
    }
  };

  useEffect(() => {
    if (isScanning) {
      setIsHovered(false);
    }
  }, [isScanning]);

  if (isScanning) return null;

  const isDisabled = isScanning || !sessionStarted;
  const showSpinner = !sessionStarted && !isScanning;
  const label = isScanning
    ? "SCANNING..."
    : !sessionStarted
    ? "Starting session..."
    : "Scan Network";

  return (
    <button
      className={`relative group px-8 py-4 rounded-full font-semibold text-lg transition-all duration-300
        ${
          isDisabled
            ? "bg-blue-600 opacity-55 text-white cursor-not-allowed"
            : "bg-blue-500/10 border border-blue-400/30 backdrop-blur-sm text-blue-900 dark:text-white hover:border-blue-400/50 hover:bg-blue-500/20"
        }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
      disabled={isDisabled}
    >
      <div className="relative z-10 flex items-center gap-3">
        <span>{label}</span>
        {showSpinner ? (
          <span className="inline-block w-4 h-4 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
        ) : !isScanning ? (
          <Wifi
            className={`w-5 h-5 transition-transform duration-300 ${
              isHovered ? "scale-110" : "scale-100"
            }`}
          />
        ) : (
          ""
        )}
      </div>

      {/* Animated rings only when enabled and not scanning */}
      {!isDisabled && !isScanning && (
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
