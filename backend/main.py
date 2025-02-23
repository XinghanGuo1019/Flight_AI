from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import uvicorn

# 创建 FastAPI 应用实例
app = FastAPI()

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 在生产环境中，将此修改为特定的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

# 定义请求模型
class ChatRequest(BaseModel):
    message: str

# 模拟的聊天处理函数
async def handle_chat(user_message: str) -> str:
    # 在这里实现与 GPT-3.5-turbo 的交互逻辑
    # 目前返回一个简单的响应作为示例
    return f"您说的是: {user_message}"

# 定义聊天接口
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    user_message = chat_request.message
    logger.info(f"Received message: {user_message}")
    try:
        response = await handle_chat(user_message)
        logger.info(f"Response: {response}")
        return {"response": response}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 运行应用
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)