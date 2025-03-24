import json
import os
from typing import Dict, List
from dotenv import load_dotenv
import openai
import psycopg2
from schemas import Flight_Change, MessageState

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

class VerificationNode:
    def __init__(self, db_host, db_name, db_user, db_password, db_port=5432):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port
        self.client = openai.OpenAI(api_key=os.getenv("CHAT_GPT_KEY"))
        self.model_id = os.getenv("CHAT_GPT_MODEL")

    def _call_gpt(self, columns: List[str], result: tuple, user_message: str) -> Dict:
        """Call OpenAI API to generate single formatted message"""
        # Build field descriptions
        if result:
            field_str = "\n".join([f"{col}: {val}" for col, val in zip(columns, result)])
        
        prompt = f"""Generate a SINGLE verification message containing:
1. Natural language confirmation or rejection in user's language.
2. If verification successful, ask user to what they would like to change for the current ticket. (eg. date, time, airport, etc.)
3. Structured details section after two newlines

The input data is as follows:
-Database results:{field_str}
-User's last message: "{user_message}"

Requirements:
- If Database results is empty, means Verification failed and No matching ticket found. Generate a message to inform user about the failure and ask user to re-input the "ticket_number", "passenger_birthday", "passenger_name" accordingly and ""intent_info"" should be "flight_change".
- If Database results is not empty, means Verification successful and matching ticket found. Generate a message by following the below requirements and ""intent_info"" should be "search_alternative".
- Use user's last message to determine the language of the confirmation message
- Use airport full names (e.g. PVG → Shanghai Pudong International Airport)
- Localize dates/times based on user's message language
- Format currency as USD with proper symbols
- Use Markdown formatting for details section
- Maintain original field names in details
- For React JSX compatibility, use <br/><br/> between confirmation and details
- Use <br/> before each detail item instead of newlines

Output JSON format:
{{
    "content": "Natural language confirmation message...<br/><br/>**Ticket Details**<br/>- Field1: Value1<br/>- Field2: Value2...",
    "sender": "system",
    "intent_info": "flight_change" or "search_alternative"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a flight ticketing assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            message = json.loads(response.choices[0].message.content)
            
            # 验证必要字段
            required_keys = ["content", "sender", "intent_info"]
            if not all(k in message for k in required_keys):
                raise ValueError(f"Missing required keys: {required_keys}")
                
            return message
        except Exception as e:
            return {
                "content": f"Verification successful. Display limited: {str(e)}",
                "sender": "system",
                "intent_info": Flight_Change
            }

    def process(self, state: MessageState) -> MessageState:
        # 从 collected_info 中提取验证所需字段
        print("====== VerificationNode Begin ======")
        new_state = state.model_copy(deep=True)
        
        ticket_number = new_state.collected_info["ticket_number"]
        passenger_birthday = new_state.collected_info["passenger_birthday"]
        passenger_name = new_state.collected_info["passenger_name"]
        # 检查必要信息是否齐全
        if not (ticket_number and passenger_birthday and passenger_name):
            new_message = {
                "content": "Verification failed: Required information is missing.",
                "sender": "system"
            }
            return {"messages": new_state.messages + new_message,
                    "collected_info": new_state.collected_info,
                    "missing_info": new_state.missing_info}

        ticket_number = new_state.collected_info["ticket_number"]
        passenger_birthday = new_state.collected_info["passenger_birthday"]
        passenger_name = new_state.collected_info["passenger_name"]

        # 连接数据库
        try:
            connection = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
        except Exception as e:
            error_msg = {"content": f"Database connection error: {str(e)}", "sender": "system"}
            new_state.messages.append(error_msg)
            return new_state

        cursor = connection.cursor()

        # 根据提供的信息查询票务表
        query = """
        SELECT ticket_number, passenger_name, passenger_birthday, airline_code,
               departure_airport, arrival_airport, departure_date, departure_time,
               arrival_date, arrival_time, return_departure_airport, return_arrival_airport,
               return_date, return_departure_time, return_arrival_date, return_arrival_time,
               price_usd
        FROM tickets
        WHERE ticket_number = %s AND passenger_birthday = %s AND passenger_name = %s;
        """
        try:
            cursor.execute(query, (ticket_number, passenger_birthday, passenger_name))
            result = cursor.fetchone()
                # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
                # Get last user message
            user_messages = [msg for msg in new_state.messages if msg["sender"] == "user"]
            last_user_msg = user_messages[-1]["content"] if user_messages else ""
                # Generate complete message through GPT
            gpt_message = self._call_gpt(columns, result, last_user_msg)               
                # Directly append the generated message
            print(f"After Verification Intent: {gpt_message["intent_info"]}")
            new_state.messages.append(gpt_message)
            if result:
                new_state.collected_info.update(
                {col: val for col, val in zip(columns, result)})
            else:
                new_state.missing_info = ["ticket_number", "passenger_birthday", "passenger_name"]
                new_state.collected_info = {}
        except Exception as e:
            new_state.messages.append( f"Database query error: {str(e)}")

        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

        return new_state
