# backend/main.py
import json
import logging
from datetime import datetime
from uuid import uuid4
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import END, StateGraph
from backend.langgraph_nodes.collect_info_node import InfoCollectionNode
from backend.langgraph_nodes.intent_detection_node import IntentDetectionNode
from backend.langgraph_nodes.search_node import SearchNode
from backend.schemas import ChatRequest, ChatResponse, MessageState
from backend.dependencies import get_settings, get_llm
from backend.chains.response import create_final_chain
from backend.utils.visualization import visualize_workflow

# 初始化日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储（生产环境建议使用Redis）
class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def get(self, session_id: str) -> Optional[MessageState]:
        if session_data := self.sessions.get(session_id):
            return MessageState(**session_data["state"])
        return None

    # 方法名从 save_session 改为 save
    def save(self, session_id: str, state: MessageState):
        self.sessions[session_id] = {
            "state": state.dict(),
            "timestamp": datetime.now()
        }

session_store = SessionStore()

def create_workflow(llm):
    """创建并返回工作流"""
    builder = StateGraph(MessageState)
    
    # 添加节点
    nodes = {
        "intent_detection_node": IntentDetectionNode(llm).process,
        "search_node": SearchNode(llm).process,
        "info_collection_node": InfoCollectionNode(llm).process,
    }
    for node_id, node_func in nodes.items():
        builder.add_node(node_id, node_func)

    # 添加等待用户输入的节点 - 这个节点在每轮对话后返回控制权给前端
    builder.add_node("awaiting_user_input", lambda state: state)
    
    # 设置固定边 - 从信息收集和一般回复节点到等待用户输入
    builder.add_edge("info_collection_node", "awaiting_user_input")
    
    # 搜索节点到结束的边 - 完成工作流
    builder.add_edge("search_node", END)
    
    # 设置入口点
    builder.set_entry_point("intent_detection_node")
    
    # 条件路由逻辑
    def route_logic(state: MessageState):
        # 获取最后一条消息的意图信息
        last_message = state.messages[-1] if state.messages else None
        # 当意图识别节点已生成回复时
        if last_message and last_message.get("sender") == "system":
            return "awaiting_user_input"  # 直接等待用户输入
        
        # 提取意图
        intent = last_message.get("intent") if last_message else None
        if intent == "flight_change":
            return "info_collection_node" if state.missing_info else "search_node"
    
        return "awaiting_user_input"  # 非改签意图直接结束流程
    
    # 添加条件边
    builder.add_conditional_edges(
        "intent_detection_node",
        route_logic,
        {
            "info_collection_node": "info_collection_node",
            "search_node": "search_node",
            "awaiting_user_input": "awaiting_user_input"
        }
    )
    
    # 从信息收集节点添加条件边，检查是否收集完毕
    def info_collection_complete(state: MessageState):
        if not state.missing_info:
            return "search_node"
        return "awaiting_user_input"
    
    builder.add_conditional_edges(
        "info_collection_node",
        info_collection_complete,
        {
            "search_node": "search_node",
            "awaiting_user_input": "awaiting_user_input"
        }
    )
    
    workflow = builder.compile()
    visualize_workflow(workflow)
    return workflow

@app.on_event("startup")
async def startup_event():
    """应用初始化"""
    settings = get_settings()
    app.state.llm = get_llm(settings)
    app.state.workflow = create_workflow(app.state.llm)
    app.state.response_chain = create_final_chain(app.state.llm)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, fastapi_request: Request):
    try:
        # 会话管理
        session_id = request.session_id or str(uuid4())
        state = session_store.get(session_id) or MessageState()

        # 初始化新状态时提供默认消息
        if not state:
            state = MessageState(
                messages=[  # ✅ 明确初始化
                    {"content": "SYSTEM_INIT", "sender": "system"}
                ],
                collected_info={},
                missing_info=[],

            )
        
        # 添加用户消息
        state.messages.append({
            "content": request.message,
            "sender": "user"
        })
        
        # 执行工作流（单步模式）
        result = await app.state.workflow.ainvoke(
            state.dict(),
            {"configurable": {"recursion_limit": 1, "interrupt_after": ["intent_detection_node"]}}  # 关键配置
        )
        requires_input = result.get("next") == "awaiting_user_input"
        # 保存新状态
        new_state = MessageState(**result)
        session_store.save(session_id, new_state)
        
        # 构建响应
        return ChatResponse(
            response=new_state.messages[-1]["content"], 
            session_id=session_id,
            requires_input=requires_input,
            flight_url=new_state.messages[-1].get("flight_url")
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)