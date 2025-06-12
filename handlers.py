from core_logic import process_message as main_logic
from openai import OpenAI
import os

def process_message(event, line_bot_api, user_sessions, registration_buffer):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    main_logic(event, line_bot_api, client, user_sessions, registration_buffer)
