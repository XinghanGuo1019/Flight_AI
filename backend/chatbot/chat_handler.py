from chatbot.response_generator import generate_response
from api.flight_api import search_flights, change_flight
from api.identity_api import verify_identity
from utils.helpers import extract_ticket_number, extract_id_number, extract_birthday, extract_flight_details

def handle_chat(user_message):
    if "change flight" in user_message.lower():
        return "Please provide your ticket number, ID number, and birthday."
    elif "ticket number" in user_message.lower():
        ticket_number = extract_ticket_number(user_message)
        id_number = extract_id_number(user_message)
        birthday = extract_birthday(user_message)
        if verify_identity(ticket_number, id_number, birthday):
            return "Identity verified. Please provide the new flight details."
        else:
            return "Identity verification failed. Please try again."
    elif "new flight" in user_message.lower():
        new_flight_details = extract_flight_details(user_message)
        if search_flights(new_flight_details['flight_number'], new_flight_details['date']):
            return "New flight found. Please confirm the change."
        else:
            return "No available flights found. Please try another date."
    elif "confirm" in user_message.lower():
        if change_flight(ticket_number, new_flight_details):
            return "Flight change successful!"
        else:
            return "Flight change failed. Please contact customer support."
    else:
        return generate_response(user_message)