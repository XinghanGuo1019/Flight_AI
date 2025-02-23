import requests
from config import Config

def verify_identity(ticket_number: str, id_number: str, birthday: str) -> bool:
    """
    验证用户身份。
    """
    url = Config.IDENTITY_VERIFICATION_API_URL
    data = {
        'ticket_number': ticket_number,
        'id_number': id_number,
        'birthday': birthday
    }
    response = requests.post(url, json=data)
    return response.json().get('success', False)