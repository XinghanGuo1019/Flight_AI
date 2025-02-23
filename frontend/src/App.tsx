import React, { useState } from "react";
import axios from "axios";
import "./style.css";

const App: React.FC = () => {
  const [message, setMessage] = useState<string>("");
  const [response, setResponse] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await axios.post("http://localhost:8000/chat", {
        message: message,
      });
      setResponse(result.data.response);
    } catch (error) {
      console.error("Error communicating with the API:", error);
      setResponse("Failed to get a response from the server.");
    }
  };

  return (
    <div className="App">
      <h1>Flight Change Chatbot</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message here..."
        />
        <button type="submit">Send</button>
      </form>
      <div className="response">
        <h3>Chatbot Response:</h3>
        <p>{response}</p>
      </div>
    </div>
  );
};

export default App;
