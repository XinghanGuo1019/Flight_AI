# intent_detection_node.py
import json
import logging
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage  # 导入 AIMessage
from schemas import FlightChangeMessage, GeneralMessage

# 配置日志
logger = logging.getLogger(__name__)

class IntentDetectionNode:
    def __init__(self, llm):
        prompt = PromptTemplate.from_template(
            """**Flight Service Agent Protocol**
    
As a flight ticketing specialist, analyze the conversation history and:

1. **Intent Identification**:
   - Recognize if the user wants to modify existing flight plans (flight_change)
   - Identify general flight-related questions (other)

2. **Response Generation**:
A) For flight_change intent:
   - List SPECIFIC missing fields from: [ticket_number, passenger_birthday, departure_date, return_date, adult_passengers]
   - Generate NATURAL request for missing info using conversation context

B) For other intents:
   - Create helpful response about flight services
   - Politely decline non-flight related requests

**Strict JSON Response Format**
```json
{{
    "intent": "flight_change" | "other",
    "missing_info": ["field1", "field2"],  // Use exact field names
    "content": "generated response text"  
}}

**Conversation History**
{messages}

**Current Response** (STRICT JSON ONLY):"""
        )
        self.chain = prompt | llm | RunnableLambda(self._parse_output)

    def _parse_output(self, text: str) -> dict:
        try:
            # 处理 AIMessage 输出
            if isinstance(text, AIMessage):
                text = text.content  # 从 AIMessage 中提取内容
            
            # 解析 JSON
            data = json.loads(text)
            
            # 验证并返回结构化数据
            if data.get("intent") == "flight_change":
                return {
                    "type": "flight_change",
                    "content": data.get("content", ""),
                    "intent_info": {
                        "intent": data.get("intent", ""),
                        "missing_info": data.get("missing_info", [])
                    },
                    "current_requirements": data.get("missing_info", [])
                }
            else:
                return {
                    "type": "general",
                    "content": data.get("content", ""),
                    "intent_info": {"intent": data.get("intent", "other")}
                }
        except Exception as e:
            logging.error(f"Failed to parse LLM output: {e}")
            return {
                "type": "general",
                "content": "抱歉，我暂时无法处理您的请求",
                "intent_info": {"intent": "other"}
            }

    async def process(self, state):
        logging.debug(f"Input state: {state}")
        
        # 直接使用 state.messages 作为聊天历史
        messages = state.messages
        
        # 调用链并记录原始输出
        raw_output = await self.chain.ainvoke({"messages": messages})
        logging.debug(f"Raw LLM output: {raw_output}")
        
        # 确保结果包含所需的键
        if "intent_info" not in raw_output:
            logging.error(f"Missing intent_info in result: {raw_output}")
            raw_output["intent_info"] = {"intent": "other"}
        
        # 动态创建消息对象
        if raw_output["type"] == "flight_change":
            new_message = FlightChangeMessage(
                content=raw_output["content"],
                intent_info=raw_output["intent_info"],
                current_requirements=raw_output.get("current_requirements", [])
            )
        else:
            new_message = GeneralMessage(
                content=raw_output["content"],
                intent_info=raw_output["intent_info"]
            )
        logging.debug(f"Output message: {new_message}")
        return {
            "messages": state.messages + [new_message.to_dict()], 
            "collected_info": state.collected_info,
            "missing_info": raw_output.get("current_requirements", [])
        }