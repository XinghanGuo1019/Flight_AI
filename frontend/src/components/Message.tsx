// src/components/Message.tsx
import React from "react";
import "../style.css";

interface MessageProps {
  sender: "user" | "assistant";
  text: string;
}

const Message: React.FC<MessageProps> = ({ sender, text }) => {
  return (
    <div className={`message ${sender}`}>
      <div className="message-content">{text}</div>
    </div>
  );
};

export default Message;
