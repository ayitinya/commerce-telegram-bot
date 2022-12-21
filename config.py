from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_KEY = getenv('API_KEY')

# bot interval and timeout
bot_interval = 3
bot_timeout = 30
current_result = ""
