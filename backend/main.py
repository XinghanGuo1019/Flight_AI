# backend/main.py
from datetime import datetime
import os
from uuid import uuid4
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from IPython.display import Image, display
from auth import get_current_user, router as auth_router

from langgraph_nodes.alternative_ticket_node import AlternativeTicketNode
from langgraph_nodes.verification_node import VerificationNode
from langgraph_nodes.await_input_node import AwaitingUserInputNode
from langgraph_nodes.collect_info_node import InfoCollectionNode
from langgraph_nodes.intent_detection_node import IntentDetectionNode
from langgraph_nodes.search_node import SearchNode
from schemas import ChatRequest, ChatResponse, Flight_Change, MessageState, Search_Alternative, Search_Flight
from dependencies import get_llm
from chains.response import create_final_chain

app = FastAPI()
app.include_router(auth_router)
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "flight_ticket_db")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "")
db_port = int(os.getenv("DB_PORT", 5432))

@app.get("/")
def read_root():
    return {"message": "Service is up!"}

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 会话存储（生产环境建议使用 Redis）
class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def get(self, session_id: str) -> Optional[MessageState]:
        if session_data := self.sessions.get(session_id):
            return MessageState(**session_data["state"])
        return None

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
        "verification_node": VerificationNode(db_host, db_name, db_user, db_password, db_port).process,
        "alternative_ticket_node": AlternativeTicketNode(llm, db_host, db_name, db_user, db_password, db_port).process
    }
    for node_id, node_func in nodes.items():
        builder.add_node(node_id, node_func)

    # 设置入口点
    builder.set_entry_point("intent_detection_node")
    builder.add_edge("verification_node", "awaiting_user_input")
    builder.add_edge("alternative_ticket_node", "awaiting_user_input")
    builder.add_edge("search_node", END)
    
    # 条件路由逻辑
    def route_logic(state: MessageState):
        if state.messages[-1]["sender"] != "user":
            return "awaiting_user_input"
        last_message = state.messages[-1] if state.messages else None
        intent_info = last_message.get("intent_info", "") if last_message else ""
        print(f"Intent Detection: {intent_info}")
        if intent_info == Search_Flight:
            if state.missing_info:
                return "info_collection_node"
            else:
                return "search_node"
        else:
            return "awaiting_user_input"
    
    builder.add_conditional_edges(
        "intent_detection_node",
        route_logic,
        {
            "info_collection_node": "info_collection_node",
            "search_node": "search_node",
            "awaiting_user_input": "awaiting_user_input"
        }
    )
    
    def info_collection_complete(state: MessageState):
        last_message = state.messages[-1] if state.messages else None
        intent_info = last_message.get("intent_info", "") if last_message else ""
        if not state.missing_info:
            if intent_info == Search_Flight:
                return "search_node"
            elif intent_info == Flight_Change:
                return "verification_node"
        return "awaiting_user_input"
    
    builder.add_conditional_edges(
        "info_collection_node",
        info_collection_complete,
        {
            "verification_node": "verification_node",
            "search_node": "search_node",
            "awaiting_user_input": "awaiting_user_input"
        }
    )

    def after_user_input_logic(state: MessageState):
        last_sys_message = next(
            (message for message in reversed(state.messages) if message.get('sender') in {'system', 'assistant'}),
            None
        )
        last_user_message = next(
            (message for message in reversed(state.messages) if message.get('sender') in {'user'}),
            None
        )
        if last_sys_message:
            intent_info = last_sys_message.get("intent_info", "")
        if last_user_message:
            user_message = last_user_message.get("content", "")
            print(f"User Message: {user_message}")
        if intent_info == Search_Flight or intent_info == Flight_Change and user_message != "Human Assistant":
            if state.missing_info:
                return "info_collection_node"
            else:
                return "search_node"
        elif intent_info == Search_Alternative and user_message != "Human Assistant":
            return "alternative_ticket_node"
        elif user_message == "Human Assistant":
            print("===End of conversation===")
            return END
        else:
            return "intent_detection_node"
    
    builder.add_conditional_edges(
        "awaiting_user_input",
        after_user_input_logic,
        {
            "info_collection_node": "info_collection_node",
            "search_node": "search_node",
            "intent_detection_node": "intent_detection_node",
            "alternative_ticket_node": "alternative_ticket_node",
        }
    )

    # def verification_complete(state: MessageState):
    #     last_message = state.messages[-1] if state.messages else None
    #     intent_info = last_message.get("intent_info", "") if last_message else ""
    #     if intent_info == Flight_Change:
    #         return "awaiting_user_input"
    #     elif intent_info == Search_Alternative:
    #         return "alternative_ticket_node"
    # builder.add_conditional_edges(
    #     "verification_node",
    #     verification_complete,
    #     {
    #         "awaiting_user_input": "awaiting_user_input",
    #         "alternative_ticket_node": "alternative_ticket_node"
    #     }
    # )
    
    workflow = builder.compile(checkpointer=memory)
    try:
        graph = workflow.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(graph)
        display(Image(graph))
    except Exception:
        print("Error drawing graph")
    return workflow

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)  # 验证令牌
):
    try:
        # 会话管理
        session_id = request.session_id or str(uuid4())
        state = session_store.get(session_id) or MessageState()

        if not state.messages:
            state = MessageState(
                messages=[{
                    "content": request.message,
                    "sender": "user"
                }],
                collected_info={},
                missing_info=[],
            )
            result = await app.state.workflow.ainvoke(
                state.dict(),
                config={"configurable": {"thread_id": session_id, "recursion_limit": 20}}
            )
        else:
            result = await app.state.workflow.ainvoke(
                Command(resume=request.message),
                config={"configurable": {"thread_id": session_id}}
            )
        new_state = MessageState(**result)
        session_store.save(session_id, new_state)
        return ChatResponse(
            response=new_state.messages[-1]["content"],
            session_id=session_id,
            flight_url=new_state.messages[-1].get("flight_url")
        )
    except Exception as e:
        if isinstance(e, KeyError) and len(e.args) > 0 and e.args[0] == '__end__':
            return ChatResponse(response="A human assistant will be with you shortly.",
                session_id=session_id)
        else:
            print(f"Chat error: {str(e)}")
            raise HTTPException(500, detail=str(e))
    
@app.on_event("startup")
async def startup_event():
    from fastapi.routing import APIRoute
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path}, Methods: {route.methods}")
    app.state.llm = get_llm()
    app.state.workflow = create_workflow(app.state.llm)
    app.state.response_chain = create_final_chain(app.state.llm)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)