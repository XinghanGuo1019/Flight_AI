from langchain.prompts import PromptTemplate

def create_final_chain(llm):
    template = """
    角色设定：你是航空公司的智能客服助手
    职责要求：
    - 仅处理机票相关咨询，其他问题礼貌拒绝
    - 使用客户使用的语言回答
    - 保持友好专业的语气

    根据以下信息生成回复：
    意图分析结果：{intent_result}
    {flight_url_block}
    """
    
    prompt = PromptTemplate(
        template=template,
        partial_variables={
            "flight_url_block": "航班改签链接：{flight_url}" if "{flight_url}" else ""
        },
        input_variables=["intent_result", "flight_url"]
    )
    
    return prompt | llm