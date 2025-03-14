import React, { useState, useEffect } from "react";
import { FaMobileAlt, FaTv, FaLaptop } from "react-icons/fa";
import { BsRouter, BsSmartwatch } from "react-icons/bs";

const getRandomPosition = () => {
  const minRadius = 30;
  const maxRadius = 45;
  const angle = Math.random() * 2 * Math.PI;
  const distance = Math.random() * (maxRadius - minRadius) + minRadius;

  return {
    x: Math.cos(angle) * distance,
    y: Math.sin(angle) * distance,
  };
};

const ScannerAnimation = () => {
  const [device, setDevice] = useState(null);

  useEffect(() => {
    const icons = [FaMobileAlt, FaTv, FaLaptop, BsRouter, BsSmartwatch];

    const generateDevice = () => {
      const Icon = icons[Math.floor(Math.random() * icons.length)];
      setDevice({
        id: Math.random(),
        Icon,
        position: getRandomPosition(),
      });
    };

    generateDevice(); // הצגת מכשיר ראשון
    const interval = setInterval(generateDevice, 2000); // שינוי כל 2 שניות

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="relative flex items-center justify-center w-25 h-25 sm:w-15 sm:h-15">
        {/* עיגולי סריקה מתרחבים (4 עיגולים) */}
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="absolute w-full h-full rounded-full border border-blue-600 
          opacity-50 animate-ping"
            style={{ animationDelay: `${i * 0.5}s`, animationDuration: "2.5s" }}
          />
        ))}

        {/* אייקון של מכשיר בודד - משתנה כל 2 שניות */}
        {device && (
          <div
            key={device.id}
            className="absolute text-blue-500 text-xs sm:text-sm opacity-90 animate-fade"
            style={{
              left: `calc(50% + ${device.position.x}px)`,
              top: `calc(50% + ${device.position.y}px)`,
            }}
          >
            <device.Icon />
          </div>
        )}

        {/* עיגול פנימי */}
        <div className="absolute w-2 h-2 sm:w-1 sm:h-1 bg-blue-500 rounded-full shadow-lg"></div>

        {/* מחוג סורק (קו מסתובב) */}
        <div
          className="absolute w-[160%] h-[2px] bg-blue-500 origin-bottom animate-spin"
          style={{
            animationDuration: "3.5s",
          }}
        ></div>
      </div>

      {/* אנימציה מותאמת לאייקונים - ללא קובץ Tailwind config */}
      <style>
        {`
          @keyframes fade {
            0%, 100% { opacity: 0; }
            50% { opacity: 0.8; }
          }
          .animate-fade {
            animation: fade 2s ease-in-out infinite;
          }
        `}
      </style>
    </div>
  );
};

export default ScannerAnimation;
