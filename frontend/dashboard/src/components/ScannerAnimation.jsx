import React from "react";

const ScannerAnimation = () => {
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
        {/* עיגול פנימי */}
        <div className="absolute w-2 h-2 sm:w-1 sm:h-1 bg-blue-500 rounded-full shadow-lg"></div>

        {/* מחוג סורק (קו מסתובב) */}
        <div
          className="absolute w-[140%] h-[2px] bg-blue-500 origin-bottom animate-spin"
          style={{
            animationDuration: "3.5s",
          }}
        ></div>
      </div>
    </div>
  );
};

export default ScannerAnimation;
