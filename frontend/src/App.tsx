// src/App.tsx
import React from "react";
import ChatBox from "./components/ChatBox";
import "./style.css";

const App: React.FC = () => {
  return (
    <div className="app">
      <h1>Smart Flight</h1>
      <ChatBox />
    </div>
  );
};

export default App;
