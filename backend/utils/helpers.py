def extract_ticket_number(message):
    # 假设票号是6位数字
    import re
    match = re.search(r'\b\d{6}\b', message)
    return match.group(0) if match else None

def extract_id_number(message):
    # 假设身份证号是18位数字
    import re
    match = re.search(r'\b\d{18}\b', message)
    return match.group(0) if match else None

def extract_birthday(message):
    # 假设生日格式为YYYY-MM-DD
    import re
    match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', message)
    return match.group(0) if match else None

def extract_flight_details(message):
    # 提取航班号和日期
    import re
    flight_number = re.search(r'\b[A-Z]{2}\d{3,4}\b', message)
    date = re.search(r'\b\d{4}-\d{2}-\d{2}\b', message)
    return {
        'flight_number': flight_number.group(0) if flight_number else None,
        'date': date.group(0) if date else None
    }