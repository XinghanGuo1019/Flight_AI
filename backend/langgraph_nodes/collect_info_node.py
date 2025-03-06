# collect_info_node.py
from datetime import datetime
import json
import logging
import re
from typing import Dict, Any, Optional, List
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from backend.schemas import MessageState, FlightInfoRequirements

logger = logging.getLogger(__name__)

class InfoCollectionNode:
    def __init__(self, llm):
        # 机场代码解析提示
        self.airport_prompt = PromptTemplate.from_template("""
        [机场代码解析指令]
        请根据用户输入执行以下操作：
        1. 识别城市名或机场代码
        2. 生成可能的IATA三字码（最多3个）
        3. 判断是否需要用户澄清
        
        输入：{user_input}
        输出格式（JSON）：
        {{
            "city": "提取的城市名",
            "possible_codes": ["代码1", "代码2"],
            "needs_clarification": boolean,
            "clarification_question": "需要澄清时的问题"
        }}
        """)
        
        # 通用字段提示模板
        self.field_prompts = {
            "ticket_number": "请输入机票票号（格式：ABC12345678）",
            "passenger_dob": "请提供出生日期（dd.mm.yyyy）",
            "departure_date": "请输入出发日期（dd.mm.yyyy）",
            "return_date": "需要返程日期吗？（输入日期或'无'）",
            "adult_passengers": "请输入成人乘客人数（1-9）"
        }
        
        # 字段验证规则
        self.validation_rules = {
            "ticket_number": {
                "pattern": r"^[A-Z]{3}\d{10}$",
                "error": "❌ 格式错误，正确示例：ABC12345678"
            },
            "departure_airport": {
                "pattern": r"^[A-Z]{3}$",
                "error": "❌ 请输入三字码（如PEK）"
            },
            "arrival_airport": {
                "pattern": r"^[A-Z]{3}$",
                "error": "❌ 请输入三字码（如PEK）"
            },
            "passenger_dob": {
                "pattern": r"\d{2}\.\d{2}\.\d{4}",
                "error": "❌ 日期格式应为dd.mm.yyyy"
            }
        }
        
        # 构建处理链
        self.airport_chain = self.airport_prompt | llm | self._parse_airport_response
        self.llm = llm

    def _parse_airport_response(self, text: str) -> Dict[str, Any]:
        """解析机场代码响应"""
        try:
            data = json.loads(text)
            return {
                "city": data.get("city", ""),
                "options": data.get("possible_codes", []),
                "needs_clarification": data.get("needs_clarification", False),
                "question": data.get("clarification_question", "")
            }
        except:
            return {"error": "无法解析机场信息"}

    async def process(self, state: MessageState) -> Dict[str, Any]:
        current_field = state.missing_info[0] if state.missing_info else None
        
        # 生成询问提示
        if not state.get("active_question"):
            question = self._generate_question(current_field)
            return {
                "messages": [{"content": question, "sender": "system"}],
                "missing_info": state.missing_info,
                "active_question": current_field
            }
        
        # 处理用户回答
        user_input = state.messages[-1].content
        validation_result = self._validate_field(current_field, user_input)
        
        if validation_result["valid"]:
            return {
                "collected_info": {**state.collected_info, **validation_result["data"]},
                "missing_info": state.missing_info[1:],
                "active_question": None
            }
        else:
            return {
                "messages": [{"content": validation_result["error"], "sender": "system"}],
                "missing_info": state.missing_info,
                "active_question": current_field
            }

    async def _process_airport_field(self, state: MessageState, field: str) -> Dict[str, Any]:
        """处理机场代码收集"""
        # 检查是否处于澄清流程中
        if hasattr(state, "airport_processing"):
            return await self._handle_airport_clarification(state, state.airport_processing, field)
            
        # 初始处理
        last_input = state.messages[-1].content  # 直接访问属性
        analysis = await self.airport_chain.ainvoke({"user_input": last_input})
        
        if analysis.get("error"):
            return self._build_error("无法识别机场信息，请直接输入三字码", field)
        
        # 自动填充唯一选项
        if len(analysis["options"]) == 1 and not analysis["needs_clarification"]:
            return self._update_state(
                state,
                field,
                analysis["options"][0],
                "auto_filled"
            )
        
        # 需要澄清
        if analysis["needs_clarification"]:
            new_state = state.model_copy()  # 使用 model_copy 复制 Pydantic 对象
            new_state.airport_processing = {
                "field": field,
                "options": analysis["options"],
                "question": analysis["question"]
            }
            return {
                "messages": [{"content": analysis["question"], "sender": "system"}],
                "state": new_state
            }
        
        return self._build_error("请输入有效的机场信息", field)

    async def _handle_airport_clarification(self, state: MessageState, ctx: Dict, field: str) -> Dict[str, Any]:
        """处理机场澄清响应"""
        user_input = state.messages[-1].content.strip()  # 直接访问属性
        
        # 处理数字选择
        if user_input.isdigit():
            choice = int(user_input) - 1
            if 0 <= choice < len(ctx["options"]):
                return self._update_state(
                    state,
                    field,
                    ctx["options"][choice],
                    "user_selected",
                    clear_context=True
                )
            return self._build_error(f"请选择1-{len(ctx['options'])}", field, retain_state=True)
        
        # 处理直接输入代码
        if re.match(r"^[A-Z]{3}$", user_input):
            return await self._validate_airport_code(state, field, user_input)
        
        return self._build_error("请输入有效选项或三字码", field, retain_state=True)

    async def _validate_airport_code(self, state: MessageState, field: str, code: str) -> Dict[str, Any]:
        """验证机场代码有效性"""
        prompt = f"机场代码 {code} 是否是真实存在的IATA代码？仅回答YES或NO。"
        response = (await self.llm.ainvoke(prompt)).strip().upper()
        
        if "YES" in response:
            return self._update_state(state, field, code, "validated")
        return self._build_error(f"无效的机场代码：{code}", field)

    async def _process_general_field(self, state: MessageState, field: str) -> Dict[str, Any]:
        """处理普通字段收集"""
        user_input = state.messages[-1].content  # 直接访问属性
        
        # 执行格式验证
        if error := self._validate_field(field, user_input):
            return self._build_error(error, field)
        
        return self._update_state(state, field, user_input)

    def _validate_field(self, field: str, value: str) -> Optional[str]:
        """验证字段格式"""
        rule = self.validation_rules.get(field)
        if not rule: return None
        if not re.match(rule["pattern"], value):
            return rule["error"]
        return None

    def _update_state(self, 
                    state: MessageState,
                    field: str,
                    value: Any,
                    source: str,
                    clear_context: bool = False) -> Dict[str, Any]:
        """更新状态通用方法"""
        new_state = state.model_copy()  # 使用 model_copy 复制 Pydantic 对象
        new_state.collected_info[field] = {
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        new_state.missing_info.remove(field)
        
        if clear_context:
            delattr(new_state, "airport_processing")  # 删除临时字段
        
        # 自动添加关联字段（例如填写出发日期后添加返程日期）
        if field == "departure_date" and not new_state.collected_info.get("return_date"):
            if "无" not in value:
                new_state.missing_info.insert(0, "return_date")
        
        return {
            "messages": [{"content": f"已更新字段：{field}", "sender": "system"}],
            "collected_info": new_state.collected_info,
            "missing_info": new_state.missing_info
        }

    def _build_error(self, 
                   message: str, 
                   field: str, 
                   retain_state: bool = False) -> Dict[str, Any]:
        """构建错误响应"""
        return {
            "messages": [{"content": message, "sender": "system", "is_error": True}],
            "collected_info": {},
            "missing_info": [field] if retain_state else []
        }