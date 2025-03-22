import os
import psycopg2
from dotenv import load_dotenv
from schemas import Flight_Change, MessageState

# 加载环境变量
load_dotenv()

class VerificationNode:
    def __init__(self, db_host, db_name, db_user, db_password, db_port=5432):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port

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
            if result:
            # 使用 cursor.description 获取列名，并构造字典
                columns = [desc[0] for desc in cursor.description]
                ticket_info = dict(zip(columns, result))
            # 将数据库中的信息更新到 collected_info
                new_state.collected_info.update(ticket_info)
                new_state.messages.append({
                    "content": f"Verification successful: Ticket found. Details: {ticket_info}",
                    "sender": "system",
                    "intent_info": Flight_Change})
            else:
                new_state.messages.append({
                    "content": "Verification failed: Ticket not found in the database.",
                    "sender": "system",
                    "intent_info": Flight_Change})
        except Exception as e:
            cursor.close()
            connection.close()
            new_state.messages.append( f"Database query error: {str(e)}")

        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()

        return new_state
