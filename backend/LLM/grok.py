import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system

# ✅ Load the environment variables from .env file
load_dotenv()

# ✅ Get the API key after loading env
client = Client(api_key=os.getenv("XAI_API_KEY"))

# ✅ Create and interact with a chat
chat = client.chat.create(model="grok-4")
chat.append(system(
    """You are Grok, a highly intelligent financial assistant. 
    When answering financial or economic questions, consider current macroeconomic factors like inflation, interest rates, and global trends — but do NOT assume fixed numerical values unless they are provided in the prompt.

Instead, use phrasing like 'given elevated inflation' or 'considering cooling price pressures' to reflect general economic conditions based on recent patterns, without assuming outdated statistics."""
))
    
chat.append(user("what is the inflation rate in us today"))

response = chat.sample()
print(response.content)
