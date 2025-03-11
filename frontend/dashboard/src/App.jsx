import React, { useState } from "react";
import Header from "./components/Header/Header";
import Sidebar from "./components/Sidebar/Sidebar";
import Main from "./UI/Main";
import Content from "./UI/Content";
import Profile from "./components/Profile/Profile";
import DeviceList from "./UI/DeviceList";

const App = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className={darkMode ? "dark" : ""}>
      <Header
        toggleDarkMode={toggleDarkMode}
        toggleSidebar={toggleSidebar}
        darkMode={darkMode}
      />
      <Sidebar isSidebarOpen={isSidebarOpen} />
      <Main>
        <Content>Main Content</Content>
        <DeviceList />
        <Profile />
      </Main>
    </div>
  );
};

export default App;
