# intent_detection_node.py
import json
import logging
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage  # 导入 AIMessage
from backend.schemas import FlightChangeMessage, GeneralMessage

# 配置日志
logger = logging.getLogger(__name__)

class IntentDetectionNode:
    def __init__(self, llm):
        prompt = PromptTemplate.from_template(
            """Imagine you are an agent, aka, customer service working for a flight ticket distribution company.\n"
    "You will take your chat history with the customer as input and respond to customer needs accordingly.\n"
    "You only reply to flight ticket related questions; for irrelevant questions, you politely refuse to answer.\n"
    "You need to answer all questions in the language the customer uses.\n\n"
            1. 分析用户对话历史，识别意图：flight_change（航班变更） 或 other（其他）
2. 若意图为 flight_change，必须返回以下JSON：
{{
    "intent": "flight_change",
    "missing_info": ["出发日期", "航班号"],  # 需要用户补充的信息
    "content": "已识别到航班变更需求，需要补充以下信息：出发日期、航班号"  # 系统提示内容
}}
3. 若为其他意图，返回：
{{
    "intent": "other",
    "content": "通用回复内容"  # 由LLM生成的正常对话回复
}}

对话历史：
{messages}

请返回严格符合上述要求的JSON："""
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