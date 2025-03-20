#schemas.py
from datetime import date
from typing import Any, Dict, List, Optional, Union, Literal
from uuid import uuid4
from loguru import logger
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    sender: str  # "user" | "assistant"
    text: str

class ChatRequest(BaseModel):
    message: str
    session_id:  Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    flight_url: str | None = None

class BaseMessage(BaseModel):
    content: str
    sender: str = "system"
    def to_dict(self):
        return self.model_dump()
    
Flight_Change = "flight_change"
Search_Flight = "search_flight"
Other_Intent = "other"

class FlightMessage(BaseMessage):
    intent_info: Literal["search_flight", "flight_change", "other"] = Other_Intent
    missing_info: List[str] = []
    flight_url: Optional[str] = None 

class GeneralMessage(BaseMessage):
    """其他意图的通用消息结构"""
    intent_info: Literal["search_flight", "flight_change", "other"] = Other_Intent

# 联合类型（按需选择一种方案）
MessageType = Union[FlightMessage, GeneralMessage]

# 状态容器
class MessageState(BaseModel):
    messages: List[Dict] = Field(
        default_factory=list,
        description="对话消息历史"
    )
    collected_info: Dict[str, Any] = Field(  # 明确字典结构
        default_factory=dict,
        description="已收集的信息"
    )
    missing_info: List[str] = Field(
        default_factory=lambda: [
            "ticket_number",
            "passenger_birthday", 
            "departure_airport",
            "arrival_airport",
            "departure_date",
            "return_date",
            "adult_passengers"
            "passenger_name"
        ],
        description="缺失信息字段"
    )
    def model_copy(self, **kwargs):
        """创建当前对象的副本"""
        return MessageState(
            messages=self.messages.copy(),
            collected_info=self.collected_info.copy(),
            missing_info=self.missing_info.copy(),
            **kwargs
        )
    
    def dict(self):
        """返回字典表示"""
        return {
            "messages": self.messages,
            "collected_info": self.collected_info,
            "missing_info": self.missing_info
        }
    def log_state(self):
        """记录当前状态"""
        logger.info(f"\n=== 当前收集状态 ===")
        logger.info(f"已收集信息: {self.collected_info}")
        logger.info(f"缺失字段: {self.missing_info}")
        logger.info(f"最新消息: {self.messages[-1]['content'] if self.messages else '无'}\n")