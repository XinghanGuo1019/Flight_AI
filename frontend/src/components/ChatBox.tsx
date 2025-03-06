import React, { useState } from "react";
import axios from "axios";
import Message from "./Message.tsx";
import { MessageInput } from "./MessageInput.tsx";
import "../style.css";

type ChatMessage = {
  sender: "user" | "assistant";
  text: string;
  flightUrl?: string; // 可选字段
};

interface ChatResponse {
  response: string;
  session_id: string;
  requires_input: boolean;
  flight_url?: string;
}

const ChatBox: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isWaiting, setIsWaiting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSend = async (userMessage: string) => {
    try {
      // 禁用输入并添加用户消息
      setIsWaiting(true);
      const userMessageObj: ChatMessage = {
        sender: "user",
        text: userMessage,
      };

      const newMessages = [...messages, userMessageObj];
      setMessages(newMessages);

      // 发送请求
      const response = await axios.post<ChatResponse>(
        "http://localhost:8000/chat",
        {
          message: userMessage,
          session_id: sessionId,
        }
      );

      // 处理响应
      const { data } = response;
      setSessionId(data.session_id);

      // 添加助理回复
      const assistantMessageObj: ChatMessage = {
        sender: "assistant",
        text: data.response,
        flightUrl: data.flight_url,
      };

      setMessages([...newMessages, assistantMessageObj]);

      // 根据 requires_input 控制输入状态
      setIsWaiting(data.requires_input);

      // 如果有机票链接则显示
      if (data.flight_url) {
        window.open(data.flight_url, "_blank");
      }
    } catch (error) {
      console.error("API 通信失败:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "assistant", text: "服务暂时不可用，请稍后重试" },
      ]);
      setIsWaiting(false);
    }
  };

  return (
    <div className="chat-box">
      <div className="messages">
        {messages.map((msg, index) => (
          <Message key={index} sender={msg.sender} text={msg.text} />
        ))}
      </div>
      <MessageInput
        onSend={handleSend}
        disabled={isWaiting}
        placeholder={isWaiting ? "正在处理您的请求..." : "请输入消息"}
      />
    </div>
  );
};

export default ChatBox;
