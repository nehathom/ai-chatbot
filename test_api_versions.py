# test_api_versions.py
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Try different API versions
api_versions = [
    "2024-02-01",
    "2023-05-15",
    "2024-08-01-preview",
    "2024-06-01",
]

for version in api_versions:
    print(f"\nTrying API version: {version}")
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=version,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="test"
        )
        print(f"✅ SUCCESS with API version {version}!")
        print(f"   Dimension: {len(response.data[0].embedding)}")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")