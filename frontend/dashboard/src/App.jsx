// import React, { useState } from "react";
// import Header from "./components/Header/Header";
// import Sidebar from "./components/Sidebar/Sidebar";
// import Main from "./UI/Main";
// import Content from "./UI/Content";
// import DeviceList from "./UI/DeviceList";

// const App = () => {
//   const [darkMode, setDarkMode] = useState(false);
//   const [isSidebarOpen, setIsSidebarOpen] = useState(false);

//   const toggleDarkMode = () => {
//     setDarkMode(!darkMode);
//   };

//   const toggleSidebar = () => {
//     setIsSidebarOpen(!isSidebarOpen);
//   };

//   return (
//     <div className={darkMode ? "dark" : ""}>
//       <Header
//         toggleDarkMode={toggleDarkMode}
//         toggleSidebar={toggleSidebar}
//         darkMode={darkMode}
//       />
//       <Sidebar isSidebarOpen={isSidebarOpen} />
//       <Main>
//         <Content>Main Content</Content>
//         <DeviceList />
//       </Main>
//     </div>
//   );
// };

// export default App;
import React, { useState, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Header from "./components/Header/Header";
import Sidebar from "./components/Sidebar/Sidebar";
import Main from "./UI/Main";
import Content from "./UI/Content";
import ControlPage from "./UI/Pages/ControlPage";
import ScanPage from "./UI/Pages/ScanPage";
import ScanTest from "./UI/Pages/ScanTest";
import FaqsPage from "./UI/Pages/FaqsPage";

const App = () => {
  // בדיקה האם יש ערך ב-localStorage עבור darkMode, אם לא - false כברירת מחדל
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("darkMode") === "true";
  });

  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Sidebar נסגר רק בלחיצה על הכפתור

  useEffect(() => {
    // שמירת מצב darkMode ב-localStorage כאשר הוא משתנה
    localStorage.setItem("darkMode", darkMode);
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode((prevMode) => !prevMode); // הפיכת המצב
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <BrowserRouter>
      <div
        className={`${
          darkMode ? "dark" : ""
        } flex flex-col min-h-screen overflow-x-hidden`}
      >
        <Header
          toggleDarkMode={toggleDarkMode}
          toggleSidebar={toggleSidebar}
          darkMode={darkMode}
          isSidebarOpen={isSidebarOpen}
        />

        <div className="flex flex-1">
          <Sidebar isSidebarOpen={isSidebarOpen} />

          {/* Main שכולל בתוכו את ה-Routes */}
          <Main>
            <Routes>
              <Route path="/" element={<Content>Main Content</Content>} />
              <Route path="/scan" element={<ScanPage />} />
              <Route path="/control" element={<ControlPage />} />
              <Route path="/scanTest" element={<ScanTest />} />
              <Route path="/faqs" element={<FaqsPage />} />
            </Routes>
          </Main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
