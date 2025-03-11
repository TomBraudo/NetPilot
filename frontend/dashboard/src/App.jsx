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

import React, { useState } from "react";
import Header from "./components/Header/Header";
import Sidebar from "./components/Sidebar/Sidebar";
import Main from "./UI/Main";
import Content from "./UI/Content";
import DeviceList from "./UI/DeviceList";

const App = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Sidebar נסגר רק בלחיצה על הכפתור

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
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
        <Main>
          <Content>Main Content</Content>
          <DeviceList />
        </Main>
      </div>
    </div>
  );
};

export default App;
