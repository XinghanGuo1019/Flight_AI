# backend/main.py
from datetime import datetime
from uuid import uuid4
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from backend.langgraph_nodes.await_input_node import AwaitingUserInputNode
from backend.langgraph_nodes.collect_info_node import InfoCollectionNode
from backend.langgraph_nodes.intent_detection_node import IntentDetectionNode
from backend.langgraph_nodes.search_node import SearchNode
from backend.schemas import ChatRequest, ChatResponse, MessageState
from backend.dependencies import get_settings, get_llm
from backend.chains.response import create_final_chain
from backend.utils.visualization import visualize_workflow


app = FastAPI()

@app.get("/test")
async def test_endpoint():
    print("\n===== TEST端点被调用 =====", flush=True)
    return {"status": "OK"}

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
    builder = StateGraph(MessageState)
    memory = MemorySaver()
    # 添加节点
    nodes = {
        "intent_detection_node": IntentDetectionNode(llm).process,
        "search_node": SearchNode(llm).process,
        "info_collection_node": InfoCollectionNode(llm).process,
        "awaiting_user_input": AwaitingUserInputNode().process,
    }
    for node_id, node_func in nodes.items():
        builder.add_node(node_id, node_func)

    # 添加等待用户输入的节点 - 这个节点在每轮对话后返回控制权给前端
    #builder.add_edge("awaiting_user_input", "intent_detection_node")
    # 设置固定边 - 从信息收集和一般回复节点到等待用户输入
    #builder.add_edge("info_collection_node", "awaiting_user_input")
    
    # 搜索节点到结束的边 - 完成工作流
    builder.add_edge("search_node", END)
    
    # 设置入口点
    builder.set_entry_point("intent_detection_node")
    
    # 条件路由逻辑
    def route_logic(state: MessageState):
        if state.messages[-1]["sender"] != "user":
            return "awaiting_user_input"  # ✅ 跳过系统消息
        # 获取最后一条消息的意图信息
        last_message = state.messages[-1] if state.messages else None
        print(f"上一条信息： {last_message}")
        
        # 添加系统回复
        intent = None
        if last_message and last_message.get("sender") == "user":
            # 仅当上一条是用户消息时才进行意图提取
            intent_info = last_message.get("intent_info", {})
            intent = intent_info.get("intent") if intent_info else None
        
        # 直接从消息中获取意图 (如果已由 intent_detection_node 添加)
        if not intent and last_message:
            intent_info = last_message.get("intent_info", {})
            intent = intent_info.get("intent") if isinstance(intent_info, dict) else None
        
        print(f"检测到的意图: {intent}")
        
        # 根据意图决定下一步
        if intent == "flight_change":
            # 如果是改签意图，检查是否需要收集信息
            if state.missing_info:
                print("进入信息收集节点")
                return "info_collection_node"
            else:
                print("信息已完整，进入搜索节点")
                return "search_node"
        else:
            # 非改签意图，等待用户输入
            print("非改签意图，等待用户输入")
            return "awaiting_user_input"
    
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

    def after_user_input_logic(state: MessageState):
        last_sys_message = next(
            (message for message in reversed(state.messages) if message.get('sender') in {'system', 'assistant'}),
        None
        )
        if last_sys_message:
            intent_info = last_sys_message.get("intent_info", {})
            intent = intent_info.get("intent") if intent_info else None
        print(f"+++++++++++++++等待之后last message: {last_sys_message}")
        if intent == "flight_change":
            if state.missing_info:
                return "info_collection_node"
            else:
                return "search_node"
        else:
            return "intent_detection_node"
    
    builder.add_conditional_edges(
        "awaiting_user_input",
        after_user_input_logic,
        {
            "info_collection_node": "info_collection_node",
            "search_node": "search_node",
            "intent_detection_node": "intent_detection_node"
        }
    )
    
    workflow = builder.compile(checkpointer=memory)
    visualize_workflow(workflow)
    return workflow

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, fastapi_request: Request):
    try:      
        # 会话管理
        session_id = request.session_id or str(uuid4())
        state = session_store.get(session_id) or MessageState()
        print("\n===== 收到新请求 =====")
        print(f"原始输入: {state}")
        # 初始化新状态时提供默认消息
        if not state.messages:
            state = MessageState(
                messages=[ 
                    {"content": request.message,
                    "sender": "user"}],
                collected_info={},
                missing_info=[],
            )
            result = await app.state.workflow.ainvoke(
            state.dict(),
            config={"configurable": {"thread_id": session_id, "recursion_limit": 20}} 
        )
        else:        
            result = await app.state.workflow.ainvoke(
                Command(resume=request.message),  # ✅ 关键恢复指令
                config={"configurable": {"thread_id": session_id}}
            )

        # 保存新状态
        new_state = MessageState(**result)
        session_store.save(session_id, new_state)
        
        # 构建响应
        return ChatResponse(
            response=new_state.messages[-1]["content"], 
            session_id=session_id,
            flight_url=new_state.messages[-1].get("flight_url")
        )
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(500, detail=str(e))
    
@app.on_event("startup")
async def startup_event():
    from fastapi.routing import APIRoute
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"Path: {route.path}, Methods: {route.methods}")
    settings = get_settings()
    app.state.llm = get_llm(settings)
    app.state.workflow = create_workflow(app.state.llm)
    app.state.response_chain = create_final_chain(app.state.llm)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)