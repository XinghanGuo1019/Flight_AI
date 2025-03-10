# backend/langgraph_nodes/awaiting_user_input_node.py
from backend.schemas import MessageState


class AwaitingUserInputNode:
    def __init__(self):
        pass
        
    def process(self, state: MessageState) -> MessageState:
        print("\n=== 进入等待节点 ===", flush=True)
        print(f"当前消息状态: {state.messages[-1] if state.messages else None}")
        return state