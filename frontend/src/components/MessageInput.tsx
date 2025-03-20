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

  // 修改后的系统消息处理
  const handleSystemMessage = () => {
    if (disabled) return;

    // 添加确认对话框
    const confirmation = window.confirm(
      "Are you sure you want to request a Human Assistant?"
    );

    if (confirmation) {
      onSend("Human Assistant");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
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

      <button
        type="button"
        className="system-button"
        onClick={handleSystemMessage}
        disabled={disabled}
      >
        Human Assistant
      </button>

      <button type="submit" disabled={disabled}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
};
