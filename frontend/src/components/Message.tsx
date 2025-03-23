// src/components/Message.tsx
import React from "react";
import "../styles/ChatBox.css";

interface MessageProps {
  sender: "user" | "assistant" | "system";
  text: string;
  flightUrl?: string; // 新增可选属性
}

const Message: React.FC<MessageProps> = ({ sender, text, flightUrl }) => {
  return (
    <div className={`message ${sender}`}>
      <div className="message-content">
        <div dangerouslySetInnerHTML={{ __html: text }} />
        {flightUrl && (
          <a href={flightUrl} target="_blank" rel="noopener noreferrer">
            See flight details
          </a>
        )}
      </div>
    </div>
  );
};

export default Message;
