// // import React, { useState } from "react";
// // import Header from "./components/Header/Header";
// // import Sidebar from "./components/Sidebar/Sidebar";
// // import Main from "./UI/Main";
// // import Content from "./UI/Content";
// // import DeviceList from "./UI/DeviceList";

// // const App = () => {
// //   const [darkMode, setDarkMode] = useState(false);
// //   const [isSidebarOpen, setIsSidebarOpen] = useState(false);

// //   const toggleDarkMode = () => {
// //     setDarkMode(!darkMode);
// //   };

// //   const toggleSidebar = () => {
// //     setIsSidebarOpen(!isSidebarOpen);
// //   };

// //   return (
// //     <div className={darkMode ? "dark" : ""}>
// //       <Header
// //         toggleDarkMode={toggleDarkMode}
// //         toggleSidebar={toggleSidebar}
// //         darkMode={darkMode}
// //       />
// //       <Sidebar isSidebarOpen={isSidebarOpen} />
// //       <Main>
// //         <Content>Main Content</Content>
// //         <DeviceList />
// //       </Main>
// //     </div>
// //   );
// // };

// // export default App;
// import React, { useState, useEffect } from "react";
// import { BrowserRouter, Route, Routes } from "react-router-dom";
// import Header from "./components/Header/Header";
// import Sidebar from "./components/Sidebar/Sidebar";
// import Main from "./UI/Main";
// import Content from "./UI/Content";
// import ControlPage from "./UI/Pages/ControlPage";
// import ScanPage from "./UI/Pages/ScanPage";
// import ScanTest from "./UI/Pages/ScanTest";
// import FaqsPage from "./UI/Pages/FaqsPage";
// import Dashboard from "./UI/Pages/Dashboard";

// const App = () => {
//   // בדיקה האם יש ערך ב-localStorage עבור darkMode, אם לא - false כברירת מחדל
//   const [darkMode, setDarkMode] = useState(() => {
//     return localStorage.getItem("darkMode") === "true";
//   });

//   const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Sidebar נסגר רק בלחיצה על הכפתור

//   useEffect(() => {
//     // שמירת מצב darkMode ב-localStorage כאשר הוא משתנה
//     localStorage.setItem("darkMode", darkMode);
//   }, [darkMode]);

//   const toggleDarkMode = () => {
//     setDarkMode((prevMode) => !prevMode); // הפיכת המצב
//   };

//   const toggleSidebar = () => {
//     setIsSidebarOpen(!isSidebarOpen);
//   };

//   return (
//     <BrowserRouter>
//       <div
//         className={`${
//           darkMode ? "dark" : ""
//         } flex flex-col min-h-screen overflow-x-hidden`}
//       >
//         <Header
//           toggleDarkMode={toggleDarkMode}
//           toggleSidebar={toggleSidebar}
//           darkMode={darkMode}
//           isSidebarOpen={isSidebarOpen}
//         />

//         {/* <Dashboard /> */}
//         <div className="flex flex-1">
//           <Sidebar isSidebarOpen={isSidebarOpen} />

//           <Main>
//             <Routes>
//               <Route path="/" element={<Dashboard />} />
//               <Route path="/scan" element={<ScanPage />} />
//               <Route path="/control" element={<ControlPage />} />
//               <Route path="/scanTest" element={<ScanTest />} />
//               <Route path="/faqs" element={<FaqsPage />} />
//             </Routes>
//           </Main>
//         </div>
//       </div>
//     </BrowserRouter>
//   );
// };

// export default App;

import React, { useState, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Header from "./components/Header/Header";
import Sidebar from "./components/Sidebar/Sidebar";
import ControlPage from "./UI/Pages/ControlPage";
import ScanPage from "./UI/Pages/ScanPage";
import ScanTest from "./UI/Pages/ScanTest";
import FaqsPage from "./UI/Pages/FaqsPage";
import Dashboard from "./UI/Pages/Dashboard";

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
        <div className="flex">
          {/* Sidebar (קבוע בצד שמאל) */}

          <aside className="fixed top-0 left-0 h-screen w-64 z-40">
            <Sidebar isSidebarOpen={isSidebarOpen} />
          </aside>

          {/* Main layout (כולל Header ותוכן) */}
          <div className="flex-1 flex flex-col min-h-screen ml-64">
            {/* Header (פרוס על כל הרוחב עם רקע מטושטש) */}
            <header className="fixed top-0 left-0 right-0 h-16 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
              <div className="pl-64 pr-4 h-full flex items-center justify-between">
                <Header
                  toggleDarkMode={toggleDarkMode}
                  toggleSidebar={toggleSidebar}
                  darkMode={darkMode}
                  isSidebarOpen={isSidebarOpen}
                />
              </div>
            </header>

            {/* Main page content (מתחת ל-Header ומימין ל-Sidebar) */}
            <main className="pt-16 bg-gray-100 dark:bg-gray-900 min-h-screen">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/scan" element={<ScanPage />} />
                <Route path="/control" element={<ControlPage />} />
                <Route path="/scanTest" element={<ScanTest />} />
                <Route path="/faqs" element={<FaqsPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
