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
from backend.langgraph_nodes.general_response_node import GeneralResponseNode
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
        "url_generation_node": SearchNode(llm).process,
        "info_collection_node": InfoCollectionNode(llm).process,
        "general_response_node": GeneralResponseNode(llm).process
    }
    for node_id, node_func in nodes.items():
        builder.add_node(node_id, node_func)

    builder.add_node("awaiting_user_input", lambda state: state)
    
    # 设置固定边
    # 新增等待状态转移
    builder.add_edge("info_collection_node", "awaiting_user_input")
    builder.add_edge("general_response_node", "awaiting_user_input")
    builder.add_edge("url_generation_node", "awaiting_user_input")
    builder.add_edge("url_generation_node", END)

    builder.set_entry_point("intent_detection_node")
    
    # 条件路由（优化版）
    def route_logic(state: MessageState):
        # 意图判断路由
        last_message = state.messages[-1] if state.messages else None
        intent = getattr(last_message, "intent_info", {}).get("intent")
        
        if intent == "flight_change":
            return "info_collection_node" if state.missing_info else "url_generation_node"
        return "general_response_node"
    builder.add_conditional_edges(
        "intent_detection_node",
        route_logic,
        {
            "info_collection_node": "info_collection_node",
            "url_generation_node": "url_generation_node",
            "general_response_node": "general_response_node"
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
            {"configurable": {"recursion_limit": 1}}  # 关键配置
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