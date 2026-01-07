# check_deployment.py
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Current Configuration ===")
print(f"AZURE_OPENAI_EMBEDDING_DEPLOYMENT: '{os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT')}'")
print(f"AZURE_OPENAI_CHAT_DEPLOYMENT: '{os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')}'")
print(f"API_VERSION: '{os.getenv('AZURE_OPENAI_API_VERSION')}'")