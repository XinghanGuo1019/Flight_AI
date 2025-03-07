# search_node.py
import logging
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config import Settings
from langchain.schema import HumanMessage
from langchain_core.runnables import RunnableLambda

logger = logging.getLogger(__name__)
settings = Settings()
api_key = settings.openai_api_key
llm = OpenAI(api_key=api_key)

class SearchNode:
    def __init__(self, llm):
        self.llm = llm
        url_template = """
        请根据以下已收集的信息，生成一个有效的机票搜索URL：
        
        出发地: {departure_airport}
        目的地: {arrival_airport}
        出发日期: {departure_date}
        返程日期: {return_date}
        成人乘客数: {adult_passengers}
        
        使用以下格式生成URL:
        https://www.skyscanner.de/transport/flights/{departure_code}/{destination_code}/{departure_date}/{return_date}/?adults={adult_count}&cabinclass=economy
        
        日期格式应为YYMMDD。
        仅返回生成的URL，不要添加任何说明或解释。
        """
        self.url_prompt = PromptTemplate.from_template(url_template)
        self.url_chain = self.url_prompt | llm
    
    async def process(self, state: dict) -> dict:
        logger.debug(f"Input state: {state}")
        # 创建新状态副本
        new_state = state.model_copy()
        
        # 准备URL生成所需信息
        collected_info = new_state.collected_info
        
        # 检查是否有所有必要的信息
        required_fields = ["departure_airport", "arrival_airport", "departure_date"]
        for field in required_fields:
            if field not in collected_info:
                new_state.messages.append({
                    "content": f"缺少必要信息：{field}",
                    "sender": "system"
                })
                return new_state.dict()
        
        # 处理日期格式转换等逻辑
        # ...
        
        # 生成URL
        url_input = {
            "departure_airport": collected_info.get("departure_airport"),
            "arrival_airport": collected_info.get("arrival_airport"),
            "departure_date": collected_info.get("departure_date"),
            "return_date": collected_info.get("return_date", ""),
            "adult_passengers": collected_info.get("adult_passengers", 1)
        }
        
        url = await self.url_chain.ainvoke(url_input)
        
        # 添加URL到消息中
        new_state.messages.append({
            "content": "已为您找到以下航班选项，请点击链接查看：",
            "sender": "system", 
            "flight_url": url.strip()
        })
        
        return new_state.dict()
