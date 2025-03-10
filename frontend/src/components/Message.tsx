// src/components/Message.tsx
import React from "react";
import "../style.css";

interface MessageProps {
  sender: "user" | "assistant" | "system";
  text: string;
  flightUrl?: string; // 新增可选属性
}

const Message: React.FC<MessageProps> = ({ sender, text, flightUrl }) => {
  return (
    <div className={`message ${sender}`}>
      <div className="content">
        {text}
        {flightUrl && (
          <a href={flightUrl} target="_blank" rel="noopener noreferrer">
            查看机票详情
          </a>
        )}
      </div>
    </div>
  );
};

export default Message;
