import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

keys_env = os.getenv("GEMINI_API_KEYS")
if keys_env:
    try:
        keys = json.loads(keys_env)
    except json.JSONDecodeError:
        keys = []
else:
    keys = []

if not keys:
    single_key = os.getenv("GEMINI_API_KEY")
    if single_key:
        keys = [single_key]

if not keys:
    raise ValueError("No Gemini API keys found. Set GEMINI_API_KEYS or GEMINI_API_KEY.")

genai.configure(api_key=keys[0])

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
