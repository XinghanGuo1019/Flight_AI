# general_response_node.py
import logging
from langchain.prompts import PromptTemplate
from backend.schemas import GeneralMessage

# 配置日志
logger = logging.getLogger(__name__)

class GeneralResponseNode:
    def __init__(self, llm):
        self.template = """
        您当前的咨询内容：{query}
        生成符合以下要求的回复：
        - 礼貌拒绝非机票相关问题
        - 使用用户原语言回复
        - 保持友好语气
        
        示例回复：
        "您好，关于机票改签和预订的问题我可以帮您解答。"
        """
        self.chain = PromptTemplate.from_template(self.template) | llm

    async def process(self, state):
        logger.debug(f"Input state: {state}")
        
        # 获取最后一条消息
        last_input = state.messages[-1]
        
        # 调用 LLM 生成回复
        response = await self.chain.ainvoke({"query": last_input})
        
        # 创建新的消息对象
        new_message = GeneralMessage(
            content=response.content,
            sender="assistant",
            intent_info=None  # 如果没有意图信息，可以设置为 None
        )
        logger.debug(f"Output message: {new_message}")
        
        # 返回更新后的状态
        return {
            "messages": state.messages + [new_message.to_dict()],  # 使用列表拼接，而不是 append
            "collected_info": state.collected_info,  # 直接访问属性
            "missing_info": state.missing_info,  # 直接访问属性
        }