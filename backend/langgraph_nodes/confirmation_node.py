# confirmation_node.py
import json
from loguru import logger
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from schemas import GeneralMessage

class ConfirmationNode:
    def __init__(self, llm):
        self.llm = llm
        confirmation_template = """
        You are a flight booking confirmation specialist. Analyze the user's latest messages to determine their intent and generate appropriate responses.

        **Message History**:
        {message_history}

        **Task**:
        1. Analyze the user's latest message to determine their intent
        2. Generate a JSON response with the following structure:
        {{
            "intent_info": "flight_change" | "change_confirmed",
            "sender": "system",
            "content": "generated response text"
        }}

        **Response Rules**:
        - If user message is "Confirm Change":
            - intent_info: "change_confirmed"
            - content: "Your flight change has been confirmed. You will receive a confirmation email shortly."
        
        - If user message is "Re-search":
            - intent_info: "flight_change"
            - content: "We will continue searching for alternative flight options based on your request."

        **Output Requirements**:
        - Response must be strict JSON format
        - Do NOT include any markdown formatting
        - Use natural, friendly language
        - Keep responses under 50 words
        """

        self.confirmation_prompt = PromptTemplate.from_template(confirmation_template)
        self.parser = JsonOutputParser()
        self.confirmation_chain = self.confirmation_prompt | llm | self.parser

    async def process(self, state: dict) -> dict:
        print("====== ConfirmationNode Begin =====")
        new_state = state.copy(deep=True)
        try:
            chain_input = {
                "message_history": new_state.messages,
            }

            # 调用大模型生成响应
            result = await self.confirmation_chain.ainvoke(chain_input)
            new_state.messages.append(result)
            return new_state

        except Exception as e:
            logger.error(f"Confirmation processing failed: {str(e)}")
            error_message = GeneralMessage(
                content=f"System error: {str(e)}",
            )
            new_state.messages.append(error_message.to_dict())
            return new_state