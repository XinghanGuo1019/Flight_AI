#search_node.py
from loguru import logger
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from schemas import FlightMessage, GeneralMessage, Search_Flight

class SearchNode:
    def __init__(self, llm):
        self.llm = llm
        url_template = """
        You are a professional flight ticketing assistant who answers all questions in the language of user input. Your task is to generate a valid flight search URL based on the collected information. Follow these rules strictly:

1. **Input Information**:
   - Departure Airport: {departure_airport}
   - Arrival Airport: {arrival_airport}
   - Departure Date: {departure_date}
   - Return Date: {return_date}
   - Adult Passengers: {adult_passengers}

2. **Data Format Rules**:
   - `departure_airport`: IATA 3-letter code (e.g., FRA for Frankfurt).
   - `arrival_airport`: IATA 3-letter code (e.g., PEK for Beijing).
   - `departure_date`: Date in `yymmdd` format.
   - `return_date`: Date in `yymmdd` format or "None" if not applicable.
   - `adult_passengers`: Number of adults (1-9).

   If any input does not match the required format, automatically convert it to the correct format.

3. **Output Format**:
   - Return a strict JSON object with two fields: `content` and `flight_url`.
   - If the URL cannot be generated, provide the reason in the `content` field and set `flight_url` to `null`.
   - If the URL is successfully generated, include the URL in the `flight_url` field and provide a natural language response in the `content` field.

4. **URL Generation Rules**:
   - Use the following URL format:
     ```
     https://www.skyscanner.de/transport/flights/{departure_airport}/{arrival_airport}/{departure_date}/{return_date}/?adultsv2={adult_passengers}&cabinclass=economy
     ```

5. **Example Output**:
   - If the URL is generated successfully:
     ```json
     {{
       "content": "Your flight search URL has been successfully generated. Click the link to view available flights.",
       "sender": "system",
       "flight_url": "https://www.skyscanner.de/transport/flights/FRA/PEK/250903/250925/?adultv2=1&cabinclass=economy"
     }}
     ```
   - If the URL cannot be generated:
     ```json
     {{
       "content": "Error: The return date is missing. Please provide a valid return date or set it to 'None'.",
       "sender": "system",
       "flight_url": null
     }}
     ```

6. **Instructions**:
   - Always validate the input data and ensure it adheres to the required formats.
   - If any required field is missing or invalid, return an error message in the `content` field and set `flight_url` to `null`.
   - Do not include any additional explanations or notes outside the JSON object.
        """
        self.url_prompt = PromptTemplate.from_template(url_template)
        self.parser = JsonOutputParser()
        self.url_chain = self.url_prompt | llm | self.parser

    async def process(self, state: dict) -> dict:
        print("====== SearchNode Begin ======")
        # 创建新状态副本
        new_state = state.copy(deep=True)

        # 准备URL生成所需信息
        collected_info = new_state.collected_info
        print(f"Collected Info: {collected_info}")
        # 生成URL
        url_input = {
            "departure_airport": collected_info['departure_airport'],
            "arrival_airport": collected_info['arrival_airport'],
            "departure_date": collected_info['departure_date'],
            "return_date": collected_info['return_date'],  
            "adult_passengers": collected_info['adult_passengers']
        }

        try:
            # 调用大模型生成URL
            url_result = await self.url_chain.ainvoke(url_input)
            print(f"Generated URL Result: {url_result}")

            # 检查URL生成结果
            if not isinstance(url_result, dict) or "content" not in url_result or "flight_url" not in url_result:
                raise ValueError("Invalid JSON response from the search node model.")
            
            if url_result.get("flight_url"):
                new_message = FlightMessage(
                    content=url_result.get("content"),
                    intent_info=Search_Flight,
                    missing_info=[],
                    flight_url=url_result.get("flight_url"),)
            else:
                new_message = GeneralMessage(
                    content=url_result.get("content"),
            )
            return {"messages": state.messages + [new_message.to_dict()],
                    "collected_info": state.collected_info,
                    "missing_info": state.missing_info}

        except Exception as e:
            logger.error(f"URL generation failed: {str(e)}")
            # 添加错误信息到消息中
            new_state["messages"].append({
                "content": f"Error: {str(e)}",
                "sender": "system"
            })
            return new_state