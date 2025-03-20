# backend/langgraph_nodes/awaiting_user_input_node.py
from schemas import MessageState
from langgraph.types import Command, interrupt

class AwaitingUserInputNode:
    def __init__(self):
        pass
        
    def process(self, state: MessageState) -> MessageState:
        print("===Awaiting User Input===")
        # 首次进入时触发中断，向客户端发送提示
        user_input = interrupt(
            value={
                "type": "await_input",
                "message": "请提供更多信息"  # 自定义提示内容
            }
        )
        print(f"===User Input: {user_input}===")
        # 恢复执行时处理用户输入（此时user_input为前端传回的值）
        return {
            "messages": state.messages + [{
                "content": user_input,
                "sender": "user"
            }],
            "collected_info": state.collected_info.copy(), 
            "missing_info": state.missing_info.copy() 
        }