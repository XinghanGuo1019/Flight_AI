import os
class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    FLIGHT_SEARCH_API_URL = 'https://api.yourflightsearch.com/search'
    IDENTITY_VERIFICATION_API_URL = 'https://api.youridentityverification.com/verify'
    FLIGHT_CHANGE_API_URL = 'https://api.yourflightchange.com/change'