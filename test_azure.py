import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

try:
    response = client.embeddings.create(
        input="Hello, Azure OpenAI!",
        model="text-embedding-ada-002"
    )
    print("✅ Azure OpenAI connection successful!")
    print(f"Embedding dimension: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"❌ Error: {e}")