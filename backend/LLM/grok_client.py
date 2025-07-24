# backend/LLM/grok_client.py

import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
import tiktoken

# Load API key from .env
load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY is not set in the .env file")

client = Client(api_key=XAI_API_KEY)

# Token counter
def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def generate_grok_insight(prompt: str, return_usage: bool = False) -> dict | str:
    try:
        chat = client.chat.create(model="grok-4")
        chat.append(system("You are a financial analyst. Be concise, helpful, and insightful."))
        chat.append(user(prompt))

        response = chat.sample()
        insight = response.content.strip()

        if return_usage:
            input_tokens = count_tokens(prompt)
            output_tokens = count_tokens(insight)
            total_tokens = input_tokens + output_tokens

            return {
                "text": insight,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
            }

        return insight

    except Exception as e:
        print("🔴 Grok LLM Error:", e)
        if return_usage:
            return {
                "text": f"Insight generation failed: {str(e)}",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        return f"Insight generation failed: {str(e)}"
