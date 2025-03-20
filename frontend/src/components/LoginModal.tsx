// src/components/LoginModal.tsx
import React, { useState } from "react";
import axios from "axios";
import "../styles/LoginModal.css";

interface LoginModalProps {
  onLoginSuccess: (token: string) => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 使用 URLSearchParams 模拟 form-data 提交（OAuth2PasswordRequestForm 默认解析这种格式）
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await axios.post(
        "http://localhost:8000/login",
        //"https://flight-ai-zhhc.onrender.com/login",
        formData
      );
      const { access_token } = response.data;
      onLoginSuccess(access_token);
    } catch (err) {
      setError("login failed");
    }
  };

  return (
    <div className="login-modal-container">
      <form className="login-form" onSubmit={handleLogin}>
        <h2 className="login-title">Sign in to Your Account</h2>
        {error && <p className="login-error">{error}</p>}
        <div className="input-group">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="login-input"
          />
        </div>
        <div className="input-group">
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
          />
        </div>
        <button type="submit" className="login-button">
          Login
        </button>
      </form>
    </div>
  );
};

export default LoginModal;
