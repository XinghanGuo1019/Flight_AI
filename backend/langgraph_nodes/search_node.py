# search_node.py
import logging
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ..config import Settings
from langchain.schema import HumanMessage
from langchain_core.runnables import RunnableLambda

logger = logging.getLogger(__name__)
settings = Settings()
api_key = settings.openai_api_key
llm = OpenAI(api_key=api_key)

url_template = (
    "根据以下对话记录，假设用户已经提供了所有必要信息（出发地、目的地、出发日期、返程日期、舱位等级、乘客人数），"
    "请生成符合格式的 Skyscanner 机票搜索 URL，格式为：\n"
    "https://www.skyscanner.de/transport/flights/{departure_code}/{destination_code}/{departure_date}/{return_date}/?adults={adult_count}&adultsv2={adult_count}&cabinclass={cabin_class}&children={children_count}&childrenv2={children_age}&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=true&ref=home&rtn=1\n"
    "如果信息不全，请返回空字符串。\n"
    "对话记录：{chat_history}"
)
url_prompt = PromptTemplate(
    input_variables=["chat_history"],
    template=url_template
)

class SearchNode:
    def __init__(self, llm):
        self.llm = llm
        self.url_chain = url_prompt | llm
    
    async def process(self, state: dict) -> dict:
        logger.debug(f"Input state: {state}")
        chat_history = state.get("chat_history", "")
        human_message = HumanMessage(content=chat_history)
        url = await self.url_chain.ainvoke(human_message)
        url = url.strip()
        logger.info(f"生成 URL: {url}")
        # 将生成的 URL 作为新的消息附加到状态中
        new_message = {
            "content": "Flight URL generated",
            "sender": "system",
            "flight_url": url
        }.to_dict()
        logger.debug(f"Output message: {new_message}")
        state["messages"].append(new_message)
        return state
