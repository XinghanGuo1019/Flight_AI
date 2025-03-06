# dependencies.py
import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from backend.config import Settings

logger = logging.getLogger(__name__)

# 配置加载 ========================================================
def get_settings() -> Settings:
    """加载应用配置（带错误处理）"""
    try:
        return Settings()  # 自动从环境变量/.env加载
    except Exception as e:
        logger.critical("配置加载失败: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="服务器配置错误，请联系管理员"
        ) from e

# LLM 核心依赖 ====================================================
def get_llm(settings: Annotated[Settings, Depends(get_settings)]) -> ChatOpenAI:
    """获取LangChain OpenAI实例（同步）"""
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY未配置")
        raise HTTPException(
            status_code=500,
            detail="服务未正确配置"
        )
    
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.model_name,
        temperature=0.3,
        max_tokens=1024
    )

async def get_async_client(
    settings: Annotated[Settings, Depends(get_settings)]
) -> AsyncGenerator[AsyncOpenAI, None]:
    """获取异步OpenAI客户端（资源安全）"""
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.debug("OpenAI异步客户端初始化成功")
        yield client
    except Exception as e:
        logger.error("客户端初始化失败: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="AI服务暂时不可用"
        ) from e
    finally:
        await client.close()  # 确保关闭连接

# 类型别名（提高可读性）=============================================
SettingsDep = Annotated[Settings, Depends(get_settings)]
LLMDep = Annotated[ChatOpenAI, Depends(get_llm)]
AsyncClientDep = Annotated[AsyncOpenAI, Depends(get_async_client)]

# 数据库示例（按需扩展）=============================================
async def get_db_session():
    """数据库会话示例（伪实现）"""
    try:
        logger.debug("初始化数据库会话")
        yield "mock_session"  # 替换为真实数据库连接
    finally:
        logger.debug("关闭数据库会话")

DBSessionDep = Annotated[str, Depends(get_db_session)]