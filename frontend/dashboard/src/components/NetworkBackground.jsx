// import React, { useEffect, useRef } from "react";

// const NetworkBackground = ({ enabled = true }) => {
//   const containerRef = useRef(null);

//   useEffect(() => {
//     if (!enabled) return;

//     const container = containerRef.current;
//     const particlesContainer = document.createElement("div");
//     particlesContainer.className = "absolute inset-0 pointer-events-none z-30";
//     container.appendChild(particlesContainer);

//     const particleCount = 60;

//     for (let i = 0; i < particleCount; i++) {
//       createParticle();
//     }

//     function createParticle() {
//       const p = document.createElement("div");
//       p.className =
//         "absolute rounded-full bg-white opacity-0 pointer-events-none";
//       const size = Math.random() * 3 + 1;
//       p.style.width = `${size}px`;
//       p.style.height = `${size}px`;
//       resetParticle(p);
//       particlesContainer.appendChild(p);
//       animateParticle(p);
//     }

//     function resetParticle(p) {
//       const x = Math.random() * 100;
//       const y = Math.random() * 100;
//       p.style.left = `${x}%`;
//       p.style.top = `${y}%`;
//       p.style.opacity = "0";
//       return { x, y };
//     }

//     function animateParticle(p) {
//       const pos = resetParticle(p);
//       const duration = Math.random() * 10 + 10;
//       const delay = Math.random() * 5;

//       setTimeout(() => {
//         p.style.transition = `all ${duration}s linear`;
//         p.style.opacity = `${Math.random() * 0.3 + 0.1}`;
//         const moveX = pos.x + (Math.random() * 20 - 10);
//         const moveY = pos.y - Math.random() * 30;
//         p.style.left = `${moveX}%`;
//         p.style.top = `${moveY}%`;

//         setTimeout(() => animateParticle(p), duration * 1000);
//       }, delay * 1000);
//     }
//   }, [enabled]);

//   if (!enabled) return null;

//   return (
//     <div
//       ref={containerRef}
//       className="absolute inset-0 overflow-hidden z-0 pointer-events-none"
//     >
//       {/* Gradient spheres */}
//       {/* Sphere 1 */}
//       <div
//         className="
//   absolute w-[40vw] h-[40vw] top-[-10%] left-[-10%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
//   bg-gradient-to-br from-sky-200/30 to-blue-100/20
//   dark:from-sky-400/40 dark:to-blue-300/20
// "
//       />

//       {/* Sphere 2 */}
//       <div
//         className="
//   absolute w-[45vw] h-[45vw] bottom-[-20%] right-[-10%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
//   bg-gradient-to-tr from-blue-200/30 to-blue-100/20
//   dark:from-indigo-400/40 dark:to-cyan-300/20
// "
//       />

//       {/* Sphere 3 */}
//       <div
//         className="
//   absolute w-[30vw] h-[30vw] top-[60%] left-[20%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
//   bg-gradient-to-tr from-blue-100/20 to-blue-50/10
//   dark:from-violet-400/30 dark:to-blue-300/10
// "
//       />

//       {/* Glow (center) */}
//       <div
//         className="
//   absolute w-[40vw] h-[40vh] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl animate-pulse [animation-duration:6s]
//   bg-blue-100/10
//   dark:bg-indigo-400/15
// "
//       />

//       {/* Grid */}
//       <div
//         className="
//   absolute inset-0 z-10
//   bg-[linear-gradient(to_right,rgba(0,0,0,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(0,0,0,0.03)_1px,transparent_1px)]
//   dark:bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)]
//   bg-[40px_40px]
// "
//       />

//       {/* Noise */}
//       <div
//         className="
//   absolute inset-0 z-20 opacity-5
//   bg-[url('data:image/svg+xml,%3Csvg viewBox=%270 0 200 200%27 xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter id=%27noiseFilter%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%270.65%27 numOctaves=%273%27 stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23noiseFilter)%27/%3E%3C/svg%3E')]
// "
//       />
//     </div>
//   );
// };

// export default NetworkBackground;

import React, { useEffect, useRef } from "react";

const NetworkBackground = ({ enabled = true }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const container = containerRef.current;
    const particlesContainer = document.createElement("div");
    particlesContainer.className = "absolute inset-0 pointer-events-none z-30";
    container.appendChild(particlesContainer);

    const particleCount = 60;

    for (let i = 0; i < particleCount; i++) {
      createParticle();
    }

    function createParticle() {
      const p = document.createElement("div");
      p.className =
        "absolute rounded-full bg-white opacity-0 pointer-events-none";
      const size = Math.random() * 3 + 1;
      p.style.width = `${size}px`;
      p.style.height = `${size}px`;
      resetParticle(p);
      particlesContainer.appendChild(p);
      animateParticle(p);
    }

    function resetParticle(p) {
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      p.style.left = `${x}%`;
      p.style.top = `${y}%`;
      p.style.opacity = "0";
      return { x, y };
    }

    function animateParticle(p) {
      const pos = resetParticle(p);
      const duration = Math.random() * 10 + 10;
      const delay = Math.random() * 1;

      setTimeout(() => {
        p.style.transition = `all ${duration}s linear`;
        p.style.opacity = `${Math.random() * 0.3 + 0.1}`;
        const moveX = pos.x + (Math.random() * 20 - 10);
        const moveY = pos.y - Math.random() * 30;
        p.style.left = `${moveX}%`;
        p.style.top = `${moveY}%`;

        setTimeout(() => animateParticle(p), duration * 1000);
      }, delay * 1000);
    }
  }, [enabled]);

  if (!enabled) return null;

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 overflow-hidden z-0 pointer-events-none"
    >
      {/* Light mode base background */}
      <div className="absolute inset-0 bg-white/70 dark:bg-transparent z-0" />

      {/* Spheres */}
      <div
        className="absolute w-[40vw] h-[40vw] top-[-10%] left-[-10%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
        bg-gradient-to-br from-sky-400/50 to-blue-300/30
        dark:from-sky-400/40 dark:to-blue-300/20"
      />
      <div
        className="absolute w-[45vw] h-[45vw] bottom-[-20%] right-[-10%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
        bg-gradient-to-tr from-blue-400/40 to-blue-200/30
        dark:from-indigo-400/40 dark:to-cyan-300/20"
      />
      <div
        className="absolute w-[30vw] h-[30vw] top-[60%] left-[20%] rounded-full blur-3xl animate-pulse [animation-duration:6s]
        bg-gradient-to-tr from-blue-400/30 to-blue-200/20
        dark:from-violet-400/30 dark:to-blue-300/10"
      />

      {/* Center Glow */}
      <div
        className="absolute w-[40vw] h-[40vh] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full blur-3xl animate-pulse [animation-duration:6s]
        bg-blue-200/20 dark:bg-indigo-400/15"
      />

      {/* Noise overlay */}
      <div
        className="
          absolute inset-0 z-20 opacity-5
          bg-[url('data:image/svg+xml,%3Csvg viewBox=%270 0 200 200%27 xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter id=%27noiseFilter%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%270.65%27 numOctaves=%273%27 stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23noiseFilter)%27/%3E%3C/svg%3E')]
        "
      />
    </div>
  );
};

export default NetworkBackground;
