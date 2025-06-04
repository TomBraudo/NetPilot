import React, { useState, useEffect } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import Header from "./components/Header/Header";
import Sidebar from "./components/Sidebar/Sidebar";
import ControlPage from "./UI/Pages/ControlPage";
import ScanPage from "./UI/Pages/ScanPage";
import ScanTest from "./UI/Pages/ScanTest";
import FaqsPage from "./UI/Pages/FaqsPage";
import Dashboard from "./UI/Pages/Dashboard";
import AboutPage from "./UI/Pages/AboutPage";

const AppLayout = ({
  darkMode,
  toggleDarkMode,
  toggleSidebar,
  isSidebarOpen,
}) => {
  return (
    <div className="flex">
      {/* Sidebar (only for non-root routes) */}
      <aside className="fixed top-0 left-0 h-screen w-64 z-20">
        <Sidebar isSidebarOpen={isSidebarOpen} />
      </aside>

      <header className="fixed top-0 left-0 right-0 h-16 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 h-full flex items-center justify-between">
          <Header
            toggleDarkMode={toggleDarkMode}
            toggleSidebar={toggleSidebar}
            darkMode={darkMode}
            isSidebarOpen={isSidebarOpen}
          />
        </div>
      </header>

      <div className="flex-1 flex flex-col min-h-screen ml-64">
        <main className="pt-16 bg-gray-100 dark:bg-gray-900 min-h-screen">
          <Routes>
            <Route path="/scan" element={<ScanPage />} />
            <Route path="/control" element={<ControlPage />} />
            {/* <Route path="/scanTest" element={<ScanTest />} /> */}
            <Route path="/about" element={<AboutPage />} />
            <Route path="/faqs" element={<FaqsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const App = () => {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("darkMode") === "true";
  });
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode((prevMode) => !prevMode);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <BrowserRouter>
      <div className={darkMode ? "dark" : ""}>
        <Routes>
          {/* Root dashboard page without sidebar */}
          <Route
            path="/"
            element={
              <>
                <header className="fixed top-0 left-0 right-0 h-16 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
                  <div className="px-4 h-full flex items-center justify-between">
                    <Header
                      toggleDarkMode={toggleDarkMode}
                      toggleSidebar={toggleSidebar}
                      darkMode={darkMode}
                      isSidebarOpen={isSidebarOpen}
                    />
                  </div>
                </header>
                <main className="pt-16 bg-gray-100 dark:bg-gray-900 h-screen overflow-hidden">
                  <Dashboard />
                </main>
              </>
            }
          />

          {/* Pages that include sidebar */}
          <Route
            path="/*"
            element={
              <AppLayout
                darkMode={darkMode}
                toggleDarkMode={toggleDarkMode}
                toggleSidebar={toggleSidebar}
                isSidebarOpen={isSidebarOpen}
              />
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
};

export default App;

// import React, { useState, useEffect } from "react";
// import { BrowserRouter, Route, Routes } from "react-router-dom";
// import Header from "./components/Header/Header";
// import Sidebar from "./components/Sidebar/Sidebar";
// import ControlPage from "./UI/Pages/ControlPage";
// import ScanPage from "./UI/Pages/ScanPage";
// import ScanTest from "./UI/Pages/ScanTest";
// import FaqsPage from "./UI/Pages/FaqsPage";
// import Dashboard from "./UI/Pages/Dashboard";

// const App = () => {
//   const [darkMode, setDarkMode] = useState(() => {
//     return localStorage.getItem("darkMode") === "true";
//   });

//   const [isSidebarOpen, setIsSidebarOpen] = useState(false);

//   useEffect(() => {
//     localStorage.setItem("darkMode", darkMode);
//   }, [darkMode]);

//   const toggleDarkMode = () => {
//     setDarkMode((prevMode) => !prevMode);
//   };

//   const toggleSidebar = () => {
//     setIsSidebarOpen(!isSidebarOpen);
//   };

//   return (
//     <BrowserRouter>
//       <div className={darkMode ? "dark" : ""}>
//         <div className="flex">
//           {/* Sidebar (קבוע בצד שמאל) */}

//           <aside className="fixed top-0 left-0 h-screen w-64 z-20">
//             <Sidebar isSidebarOpen={isSidebarOpen} />
//           </aside>
//           <header className="fixed top-0 left-0 right-0 h-16 z-30 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
//             <div className="pr-4 h-full flex items-center justify-between">
//               <Header
//                 toggleDarkMode={toggleDarkMode}
//                 toggleSidebar={toggleSidebar}
//                 darkMode={darkMode}
//                 isSidebarOpen={isSidebarOpen}
//               />
//             </div>
//           </header>

//           {/* Main layout (כולל Header ותוכן) */}
//           <div className="flex-1 flex flex-col min-h-screen ml-64">
//             {/* Main page content (מתחת ל-Header ומימין ל-Sidebar) */}
//             <main className="pt-16 bg-gray-100 dark:bg-gray-900 min-h-screen">
//               <Routes>
//                 <Route path="/" element={<Dashboard />} />
//                 <Route path="/scan" element={<ScanPage />} />
//                 <Route path="/control" element={<ControlPage />} />
//                 <Route path="/scanTest" element={<ScanTest />} />
//                 <Route path="/faqs" element={<FaqsPage />} />
//               </Routes>
//             </main>
//           </div>
//         </div>
//       </div>
//     </BrowserRouter>
//   );
// };

// export default App;
