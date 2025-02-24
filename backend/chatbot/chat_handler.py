import os
import openai
from config import Config

# 设置 OpenAI API 密钥
api_key = Config.OPENAI_API_KEY

# 初始化 OpenAI 客户端
client = openai.Client(api_key=api_key)

# 初始化聊天历史记录
chat_history = []

# 定义聊天处理函数
async def handle_chat(user_message: str) -> str:
    # 将用户消息添加到聊天历史
    chat_history.append({"role": "user", "content": user_message})

    # 限制聊天历史记录最多包含10条消息
    if len(chat_history) > 10:
        chat_history.pop(0)

    # 定义系统提示
    system_prompt = (
        "Imagine you are an agent, aka, customer service working for a flight ticket distribution company. "
        "You will take your chat history with the customer as input and respond to customer needs accordingly. "
        "You only reply to flight ticket related questions; for irrelevant questions, you politely refuse to answer. "
        "You need to answer all questions in the language the customer uses."
    )

    # 将系统提示添加到聊天历史
    messages = [{"role": "system", "content": system_prompt}] + chat_history

    # 调用 OpenAI API 获取回复
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.5,
        )
        assistant_message = response.choices[0].message.content.strip()

        # 将助手的回复添加到聊天历史
        chat_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message
    except Exception as e:
        # 处理 API 调用中的异常
        raise RuntimeError(f"调用 OpenAI API 时出错: {str(e)}")