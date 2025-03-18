// src/components/ChatBox.tsx
import React, { useState } from "react";
import axios from "axios";
import Message from "./Message";
import { MessageInput } from "./MessageInput";
import "../style.css";

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

  const handleSend = async (userMessage: string) => {
    try {
      const userMessageObj: ChatMessage = {
        sender: "user",
        text: userMessage,
      };

      const tempMessages = [...messages, userMessageObj];
      setMessages(tempMessages);

      const response = await axios.post<ChatResponse>(
        // "http://localhost:8000/chat",
        "https://flight-ai-zhhc.onrender.com/chat",
        { message: userMessage, session_id: session_id },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const { data } = response;
      setSessionId(data.session_id);

      const assistantMessages: ChatMessage[] = [];
      if (data.response !== "SYSTEM_AWAIT_NEXT_INPUT") {
        assistantMessages.push({
          sender: "assistant",
          text: data.response,
          flightUrl: data.flight_url,
        });
      }

      const finalMessages = [...tempMessages, ...assistantMessages];
      setMessages(finalMessages);

      if (data.flight_url) {
        window.open(data.flight_url, "_blank");
      }
    } catch (error) {
      console.error("API 通信失败:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "assistant", text: "服务暂时不可用，请稍后重试" },
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
          />
        ))}
      </div>
      <MessageInput onSend={handleSend} disabled={false} placeholder={""} />
    </div>
  );
};

export default ChatBox;
