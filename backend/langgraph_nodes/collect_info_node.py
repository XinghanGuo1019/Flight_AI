# collect_info_node.py
from loguru import logger
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from backend.schemas import MessageState

class InfoCollectionNode:
    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional flight ticketing specialist. Your task is to collect the following information from the user:
    
Required Fields:
- ticket_number: 13-digit ticket number (e.g. ABC1234567890)
- passenger_birthday: Date in dd.mm.yyyy format
- departure_airport: IATA 3-letter code
- arrival_airport: IATA 3-letter code
- departure_date: Date in dd.mm.yyyy format
- return_date: Date in dd.mm.yyyy or "None"
- adult_passengers: Number of adults (1-9)

Current Status:
Collected Info: {{collected_info}}
Missing Fields: {{missing_info}}

Processing Rules:
1. Analyze the user's latest message and extract ALL available information if the info can be mapped to the required fields,
   put the mapped info into collected_info and remove the same field from missing_info, so that the chain can keep collecting the remaining fields.
2. For dates: Convert any format to dd.mm.yyyy (e.g. "March 5th" → 05.03.2024)
3. For airports:
   - If city name is given (e.g. "New York"), ask to specify airport code
   - Accept only valid IATA codes (e.g. JFK)
4. For ticket numbers: Auto-correct format (e.g. "Abc 123" → ABC1234567890)
5. If multiple fields are provided in one message, process all simultaneously
6. If no valid info found, politely ask for specific missing fields and do not change info in collected_info and missing_info

Response Format:
{{
    "collected_info": [updated fields],
    "missing_info": [still fields],
    "response": "Your next question/clarification"
}}""")
        ]).partial(format_instructions=self.parser.get_format_instructions())

    async def process(self, state: MessageState) -> MessageState:
        print("Info collection node BEGIN")
        new_state = state.model_copy(deep=True)
        new_state.log_state()
        
        # 仅处理用户最新消息
        last_msg = next((m for m in reversed(state.messages) if m["sender"] == "user"), None)
        if not last_msg:
            return self._gen_next_question(new_state)
            
        # 构建处理链
        chain = (
            RunnablePassthrough.assign(
                collected_info=lambda x: x["collected_info"],
                missing_info=lambda x: x["missing_info"]
            )
            | self.prompt
            | self.llm
            | self.parser
        )
        
        # 执行处理
        try:
            result = await chain.ainvoke({
                "collected_info": new_state.collected_info,
                "missing_info": new_state.missing_info,
                "input": last_msg["content"]
            })
            
            # 更新收集状态
            new_state.collected_info.update(result.get("collected_info", {}))
            new_state.missing_info = [
                f for f in new_state.missing_info 
                if f not in result.get("collected_info", {})
            ]
            print(f"Still missing info: {new_state.missing_info}")
            
            # 添加系统回复
            if response := result.get("response"):
                new_state.messages.append({
                    "content": response,
                    "sender": "system"
                })
                
        except Exception as e:
            logger.error(f"信息收集节点处理失败: {str(e)}", exc_info=True)  # 打印堆栈跟踪
            new_state.messages.append({
                "content": "系统处理出错，请重新输入",
                "sender": "system"
            })
        return new_state

    def _gen_next_question(self, state: MessageState) -> MessageState:
        """生成下一个问题"""
        new_state = state.copy()
        
        if not new_state.missing_info:
            return new_state
            
        # 优先询问票号和日期类信息
        priority_fields = ["ticket_number", "departure_date", "passenger_birthday"]
        for field in priority_fields:
            if field in new_state.missing_info:
                question = self._field_prompt(field)
                new_state.messages.append({
                    "content": question,
                    "sender": "system"
                })
                return new_state
                
        # 默认询问第一个缺失字段
        question = self._field_prompt(new_state.missing_info[0])
        new_state.messages.append({
            "content": question,
            "sender": "system"
        })
        return new_state

    def _field_prompt(self, field: str) -> str:
        """字段对应的提示语"""
        prompts = {
            "ticket_number": "请提供13位机票号码（格式示例：ABC1234567890）",
            "passenger_birthday": "请输入乘机人出生日期（dd.mm.yyyy格式）",
            "departure_airport": "请输入出发机场名称或三字码",
            "arrival_airport": "请输入到达机场名称或三字码",
            "departure_date": "请输入新的出发日期（dd.mm.yyyy格式）",
            "return_date": "请输入新的返程日期（若无返程请填'无'）",
            "adult_passengers": "请输入成人乘客人数（1-9）"
        }
        return prompts.get(field, f"请提供{field}信息")