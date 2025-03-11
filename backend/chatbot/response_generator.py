import openai
import os
from config import Config
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
llm_model = os.getenv("LLM_MODEL")

def generate_response(user_message):
    response = openai.ChatCompletion.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
    )
    return response['choices'][0]['message']['content']