// src/components/ChatBox.tsx
import React, { useState } from "react";
import axios from "axios";
import Message from "./Message";
import { MessageInput } from "./MessageInput";
import "../styles/ChatBox.css";

export type ChatMessage = {
  sender: "user" | "assistant" | "system";
  text: string;
  flightUrl?: string;
  isAwaitSignal?: boolean;
};

interface ChatResponse {
  response: string;
  session_id: string;
  flight_url?: string;
}

interface ChatBoxProps {
  token: string;
}

const ChatBox: React.FC<ChatBoxProps> = ({ token }) => {
  const [session_id, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSendMessage = (message: string) => {
    const userMessageObj: ChatMessage = {
      sender: "user",
      text: message,
      isAwaitSignal: true,
    };

    setMessages((prev) => [...prev, userMessageObj]);
    handleSend(message); // 复用现有的发送逻辑
  };

  // 修改后的handleSend方法
  const handleSend = async (userMessage: string) => {
    try {
      // 如果消息是系统自动生成的，跳过添加临时消息
      if (
        !messages.some((msg) => msg.isAwaitSignal && msg.text === userMessage)
      ) {
        const userMessageObj: ChatMessage = {
          sender: "user",
          text: userMessage,
        };
        setMessages((prev) => [...prev, userMessageObj]);
      }

      const response = await axios.post<ChatResponse>(
        "http://localhost:8000/chat",
        { message: userMessage, session_id: session_id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const { data } = response;
      setSessionId(data.session_id);

      // 处理系统响应
      if (data.response !== "SYSTEM_AWAIT_NEXT_INPUT") {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: data.response,
            flightUrl: data.flight_url,
          },
        ]);
      }

      if (data.flight_url) {
        window.open(data.flight_url, "_blank");
      }
    } catch (error) {
      console.error("API 通信失败:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "assistant", text: "Service not available" },
      ]);
    }
  };

  return (
    <div className="chat-box">
      <div className="messages">
        {messages.map((msg, index) => (
          <Message
            key={index}
            sender={msg.sender}
            text={msg.text}
            flightUrl={msg.flightUrl}
            onSendMessage={handleSendMessage} // 传递回调函数
          />
        ))}
      </div>
      <MessageInput
        onSend={handleSend}
        disabled={false}
        placeholder={"Type your message..."}
      />
    </div>
  );
};

export default ChatBox;
