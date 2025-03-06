import React from "react";
import { useState } from "react";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder: string;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSend,
  disabled,
  placeholder,
}) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!disabled && message.trim()) {
      onSend(message.trim());
      setMessage("");
    }
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "发送中..." : "发送"}
      </button>
    </form>
  );
};
