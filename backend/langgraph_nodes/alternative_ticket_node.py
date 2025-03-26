# alternative_ticket_node.py

import json
from loguru import logger
import psycopg2
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage

class AlternativeTicketNode:
    def _parse_output(self, text: str) -> str:
        try:
            if isinstance(text, AIMessage):
                text = text.content 
                text = text.replace("```sql", "")
                text = text.replace("```json", "")
                text = text.replace("```", "")
                # text = text.replace("\n", " ")
            return text
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")

    def __init__(self, llm, db_host, db_name, db_user, db_password, db_port=5432):
        self.llm = llm
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_port = db_port
        
        sql_template = """You are a database expert and you need to generate executable SQL for alternative_tickets table based on(**Output ONLY the PostgreSQL statement with ABSOLUTELY no other information.**) :
        
        # Original Ticket info:
        {collected_info}
        
        # Chat History: "{messages}"
        
        # Rules:
        1. Use exact column names from alternative_tickets table, the table schema is as follows:
            CREATE TABLE alternative_tickets (
    airline_code VARCHAR(10) NOT NULL,
    departure_airport CHAR(3) NOT NULL,
    arrival_airport CHAR(3) NOT NULL,
    departure_date VARCHAR(8),  
    departure_time TIME NOT NULL,
    arrival_date VARCHAR(8),   
    arrival_time TIME NOT NULL,
    return_departure_airport CHAR(3),
    return_arrival_airport CHAR(3),
    return_date VARCHAR(8),     
    return_departure_time TIME,
    return_arrival_date VARCHAR(8),  
    return_arrival_time TIME,
    price_usd DECIMAL(10, 2) NOT NULL
);
        2. You need to analyze the Chat History and the Original Ticket info, to find out how the user wants to change the ticket, and you need to generate PostgreSQL to find the best matching alternative tickets in alternative_tickets table.
           for example, if the user wants to change the departure date to 2 days later, you need to find the alternative tickets with the same departure airport, arrival airport, and departure time, but with a departure date +2 days. please note the date format is DDMMYYYY.
           another example, if the user says I need a cheaper flight around the same date, you need to find the alternative tickets with the same departure airport, arrival airport, with departure date range plus or minus some days but with a lower price than the Orignal Ticket.
           But do not use all the information in the Original Ticket info to generate SQL, otherwise you won't find any alternative. You need to be smart to find out which information is important to find the best matching alternative tickets
        3. Strictly follow data format provided in the Original Ticket info
        4. Include mandatory WHERE conditions
        5. Do not use airline_code or any time information or price to do the SQL 'WHERE' query, unless user input specifies like "I want to depart earlier that day" or "I want a cheaper flight".
        6. No INSERT, UPDATE, DELETE, or JOIN operations are allowed, only SELECT.
        
        **Output ONLY the PostgreSQL statement with ABSOLUTELY no other information.**"""
        
        self.sql_prompt = PromptTemplate.from_template(sql_template)
        self.sql_chain = self.sql_prompt | self.llm | RunnableLambda(self._parse_output)

    async def process(self, state: dict) -> dict:
        logger.info("====== AlternativeTicketNode Start =====")
        new_state = state.copy(deep=True)
        
        try:
            # Step 1: 生成SQL
            collected_info = new_state.collected_info
            messages = new_state.messages
            
            sql_input = {
                "collected_info": collected_info,
                "messages": messages
            }
            
            raw_sql = await self.sql_chain.ainvoke(sql_input)
            print(f"Generated SQL: {raw_sql}")

            # Step 2: 执行SQL
            results = []
            try:
                with psycopg2.connect(
                    host=self.db_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    port=self.db_port
                ) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(raw_sql)
                        results = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise

            # Step 3: 生成解读消息
            interpretation = await self._generate_interpretation(
                columns=columns,
                results=results,
                collected_info=collected_info
            )
            
            new_state.messages.append(interpretation)
            return new_state

        except Exception as e:
            new_state.messages.append({
                "content": f"System Error: {str(e)}",
                "sender": "system"
            })
            return new_state

    async def _generate_interpretation(self, columns, results, collected_info):
        """生成结果解读消息"""
        prompt_template = """
        Generate a SINGLE analysis message containing:
        1. Natural language summary in user's language, and ask if the user if the showed alternative ticket is what they are looking for, if there are several alternatives, ask the user to specify which one they want to book, and in the intent_info, you need to put "alternative_found".
        2. If there is no alternative ticket found, you need to ask user for other options, and in the intent_info, you need to put "no_alternative".
        3. Highlight best matches, analyze the Original Ticket info and compare with Sample Data and summarize the changes (highlighted in bold, be aware that the content only recognizes the html tags)
        4. Structured details section after two newlines

        Input Data:
        - Found {result_count} alternatives
        - Schema fields: {columns}
        - Alternative Tickets: {sample_data}
        - Original Ticket info: {collected_info}

        Requirements:
        - Use airport full names (e.g., JFK → John F. Kennedy International Airport)
        - Localize dates/times based on user's language
        - Format currency as USD (e.g., $450.00) and specify the price difference compared to the original ticket
        - For React compatibility:
          - Use <br/><br/> between sections
          - Use <br/> for line breaks
          - Avoid special characters

        Output should be strict JSON:
        {{
            "content": "Summary text...<br/><br/>**Options**<br/>- Field1: Value1<br/>- ...",
            "sender": "system",
            "intent_info": "alternative_found" | "no_alternative" 
        }}"""
        
        sample_data = results[:1] if results else [] 
        prompt = prompt_template.format(
            result_count=len(results),
            columns=", ".join(columns),
            sample_data=str(sample_data),
            collected_info=collected_info
        )
        
        response = await self.llm.ainvoke(prompt)
        text = response.content
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.replace("\n", "")
        data = json.loads(text)
        return data