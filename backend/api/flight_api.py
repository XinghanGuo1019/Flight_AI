import requests
from config import Config

def search_flights(flight_number, date):
    url = Config.FLIGHT_SEARCH_API_URL
    params = {'flight_number': flight_number, 'date': date}
    response = requests.get(url, params=params)
    return response.json()

def change_flight(ticket_number, new_flight_details):
    url = Config.FLIGHT_CHANGE_API_URL
    data = {'ticket_number': ticket_number, 'new_flight_details': new_flight_details}
    response = requests.post(url, json=data)
    return response.json()