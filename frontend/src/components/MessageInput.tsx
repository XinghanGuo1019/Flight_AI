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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // 防止默认行为（如表单提交）
      handleSubmit(e as unknown as React.FormEvent);
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
        onKeyDown={handleKeyDown}
      />
      <button type="submit" disabled={disabled}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
};
