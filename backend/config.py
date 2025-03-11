from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "deepseek-chat"
    
    class Config:
        env_file = ".env"
        extra = "ignore"