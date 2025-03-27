# restart_node.py
import json
from loguru import logger
from schemas import GeneralMessage, MessageState

class RestartNode:
    def __init__(self):
        # 此节点无需调用 LLM，只负责重置状态
        pass

    def process(self, state: MessageState) -> MessageState:
        print("====== RestartNode Begin =====")
        new_state = state.model_copy()

        last_message = new_state.messages[-1].copy()
            # 如果存在intent_info字段，则清除它
        if "intent_info" in last_message:
            last_message["intent_info"] = ""
        new_state.messages = [last_message]
            
        logger.info("State has been reset successfully.")
        return new_state