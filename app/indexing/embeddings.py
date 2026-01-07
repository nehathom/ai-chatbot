import os
from typing import List
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Azure OpenAI.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors
    """
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    
    # Clean and validate input texts
    clean_texts = []
    for text in texts:
        # Convert to string and strip whitespace
        clean_text = str(text).strip()
        
        # Skip empty texts
        if not clean_text:
            clean_text = "empty"
        
        # Replace problematic characters
        clean_text = clean_text.replace('\x00', '')  # Remove null bytes
        
        clean_texts.append(clean_text)
    
    # Process in batches
    embeddings = []
    batch_size = 16
    
    for i in range(0, len(clean_texts), batch_size):
        batch = clean_texts[i:i + batch_size]
        
        try:
            response = client.embeddings.create(
                model=deployment,
                input=batch
            )
            embeddings.extend([item.embedding for item in response.data])
        except Exception as e:
            print(f"Error embedding batch: {e}")
            print(f"Batch content: {batch[:100]}...")  # Print first 100 chars for debugging
            raise
    
    return embeddings