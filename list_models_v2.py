import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

with open("models_list.txt", "w", encoding="ascii") as f:
    f.write("Listing all models...\n")
    try:
        models = genai.list_models()
        for m in models:
            f.write(f"Name: {m.name}\n")
            f.write(f"Supported methods: {m.supported_generation_methods}\n")
            f.write("-" * 20 + "\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
