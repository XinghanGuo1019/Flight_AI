// src/components/ChatBox.tsx
import React, { useState } from "react";
import axios from "axios";
import Message from "./Message.tsx";
import MessageInput from "./MessageInput.tsx";
import "../style.css";

interface ChatMessage {
  sender: "user" | "assistant";
  text: string;
}

const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSend = async (userMessage: string) => {
    const newMessages: ChatMessage[] = [
      ...messages,
      { sender: "user", text: userMessage },
    ];
    setMessages(newMessages);

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        message: userMessage,
      });
      const assistantMessage = response.data.response;
      setMessages([
        ...newMessages,
        { sender: "assistant", text: assistantMessage } as ChatMessage,
      ]);
    } catch (error) {
      console.error("Error communicating with the API:", error);
      setMessages([
        ...newMessages,
        {
          sender: "assistant",
          text: "Failed to get a response from the server.",
        } as ChatMessage,
      ]);
    }
  };

  return (
    <div className="chat-box">
      <div className="messages">
        {messages.map((msg, index) => (
          <Message key={index} sender={msg.sender} text={msg.text} />
        ))}
      </div>
      <MessageInput onSend={handleSend} />
    </div>
  );
};

export default ChatBox;
