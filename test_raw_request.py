# test_raw_request.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = "text-embedding-ada-002"
api_version = "2024-02-01"

url = f"{endpoint}openai/deployments/{deployment}/embeddings?api-version={api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

data = {
    "input": "test"
}

print(f"URL: {url}")
print(f"Deployment: {deployment}")

response = requests.post(url, headers=headers, json=data)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")