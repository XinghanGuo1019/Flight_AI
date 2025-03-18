# collect_info_node.py
from loguru import logger
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..schemas import MessageState

class InfoCollectionNode:
    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional flight ticketing specialist, you answer all questions using the language of user input. Your task is to collect the following information from the user: 
Required Fields:
- ticket_number: 13-digit ticket number (e.g. ABC1234567890)
- passenger_birthday: Date in dd.mm.yyyy format
- departure_airport: IATA 3-letter code
- arrival_airport: IATA 3-letter code
- departure_date: Date in yymmdd format
- return_date: Date in yymmdd or "None"
- adult_passengers: Number of adults (1-9)
Current Status:
Collected Info: {collected_info}
Missing Fields: {missing_info}
Processing Rules:
1. Analyze the chat history {input} but ONLY extract ALL available information from last round of conversation. If the extraced info can be mapped to the required fields,
   put the mapped info into collected_info and remove the same field from missing_info, so that the chain can keep collecting the remaining fields.
   **VERY IMPORTANT**: try to understand the user's natural language input and map the input to the required fields. 
             Few-shot example, both "my birthday is 1991.10.19" or "I was born on 1991.10.19" should be mapped to "passenger_birthday". 
             Or another example: both "I want to leave on March 5th" or "I fly on March 5th" should be mapped to "departure_date". 
             The same applies to all other fields: ticket_number, departure_airport, arrival_airport, return_date, adult_passengers.
             If you are not sure about the mapping, please ask the user for clarification in "response".
2. If you mapped departure_date or return_data: Convert any format to yymmdd (e.g. "March 5th" → 240305)
3. If you mapped departure_airport or arrival_airport:
   - If city name is given (e.g. "I leave from New York") in user's input, provide all airport IATA code for New York  in "response" to user and ask user to specify airport code.
   - Accept only valid IATA codes (e.g. JFK), you as a flight ticketing specialist should check that in your memory.
4. For ticket numbers: Auto-correct format (e.g. "Abc 123" → ABC1234567890)
5. If multiple fields are provided in one message, process all simultaneously
6. **Output MUST be in valid JSON format. Do NOT return plain text.**
7. If no valid info found, politely ask for specific missing fields in "response" and do not change "collected_info" and "missing_info", but still return the response in JSON format.
**Strict JSON Response Format** should be returned and it contains the following fields:
-"collected_info": a Dict containing the collected information,
-"missing_info": a List containing the STILL missing information,
-"response": LLM's response to the user, asking for the STILL missing information or asking for clarification or indicate the completion of data collection.             
for example, if the user says "my ticket number is ABC1234567890", the ticket_number field should be added to collected_info Dict and ticket_number shoulded be removed from missing_info List.  
             """)
        ]).partial(format_instructions=self.parser.get_format_instructions())

        # 构建处理链
        self.chain = (
            RunnablePassthrough.assign(
                collected_info=lambda x: x.get("collected_info",{}),
                missing_info=lambda x: x.get("missing_info",[]),
                input=lambda x: x["input"]
            )
            | self.prompt
            | self.llm
            | self.parser
        )

    async def process(self, state: MessageState) -> MessageState:
        print("===Info collection node BEGIN===")
        new_state = state.model_copy(deep=True)
        new_state.log_state()
        
        # # 仅处理用户最新消息
        # last_msg = next((m for m in reversed(state.messages) if m["sender"] == "user"), None)
        # if not last_msg:
        #     return self._gen_next_question(new_state)
    
        
        # 执行处理
        try:
            try:
                result = await self.chain.ainvoke({
                    "collected_info": new_state.collected_info,
                    "missing_info": new_state.missing_info,
                    "input": new_state.messages
                })
                print(f"LLM 输出: {result}")
                if not isinstance(result, dict):
                    raise ValueError(f"Invalid JSON response: {result}")
            except Exception as e:
                logger.error(f"信息收集节点处理失败: {str(e)}", exc_info=True)
            
            # 更新收集状态
            new_state.collected_info.update(result.get("collected_info", {}))
            new_state.missing_info = [
                f for f in new_state.missing_info 
                if f not in result.get("collected_info", {})
            ]

            # 添加系统回复
            if response := result.get("response"):
                new_state.messages.append({
                    "content": response,
                    "sender": "system",
                    "intent_info": {"intent": "flight_change"}
                })
  
        except Exception as e:
            logger.error(f"信息收集节点处理失败: {str(e)}", exc_info=True)  # 打印堆栈跟踪
            new_state.messages.append({
                "content": "系统处理出错，请重新输入",
                "sender": "system"
            })
        return new_state