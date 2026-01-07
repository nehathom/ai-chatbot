# test_exact_deployment.py
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Try BOTH possible deployment names
test_names = [
    "text-embedding-ada-002",
    "text-embedding-3-small", 
    "text-embedding-3-large",
    os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
]

for deployment_name in test_names:
    print(f"\nTrying deployment: '{deployment_name}'")
    try:
        response = client.embeddings.create(
            model=deployment_name,
            input="test"
        )
        print(f"✅ SUCCESS with '{deployment_name}'!")
        print(f"   Dimension: {len(response.data[0].embedding)}")
        break
    except Exception as e:
        print(f"❌ Failed: {e}")