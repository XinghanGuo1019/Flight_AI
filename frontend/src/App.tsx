// src/App.tsx
import React, { useState } from "react";
import ChatBox from "./components/ChatBox";
import LoginModal from "./components/LoginModal";
import "./style.css";

const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  return (
    <div className="app">
      <h1>Smart Flight</h1>
      {token ? (
        <ChatBox token={token} />
      ) : (
        <LoginModal onLoginSuccess={setToken} />
      )}
    </div>
  );
};

export default App;
