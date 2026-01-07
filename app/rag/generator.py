import os
from typing import List, Dict
from dotenv import load_dotenv
from openai import AzureOpenAI
from app.utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def build_prompt(query: str, contexts: List[Dict]) -> str:
    """Build a prompt for the LLM using retrieved contexts."""
    context_text = "\n\n".join([
        f"[Document {i+1}]\n{ctx['text']}" 
        for i, ctx in enumerate(contexts)
    ])
    
    prompt = f"""You are a helpful AI assistant. Answer the question based on the context provided below. If the answer cannot be found in the context, say "I don't have enough information to answer that question."

Context:
{context_text}

Question: {query}

Answer:"""
    
    return prompt

def generate_answer(query: str, contexts: List[Dict]) -> Dict:
    """Generate an answer using Azure OpenAI GPT."""
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    
    logger.info(f"Generating answer for query: '{query[:50]}...'")
    logger.info(f"Using {len(contexts)} context chunks")
    
    # Build the prompt
    prompt = build_prompt(query, contexts)
    
    # Call Azure OpenAI
    logger.info(f"Calling Azure OpenAI model: {deployment}")
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on provided context. Be concise and accurate."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    answer = response.choices[0].message.content
    logger.info(f"Generated answer ({len(answer)} characters)")
    
    # Convert contexts to JSON-serializable format
    serializable_contexts = []
    for ctx in contexts:
        serializable_ctx = {
            "chunk_id": ctx.get("chunk_id", ""),
            "text": ctx.get("text", ""),
            "metadata": ctx.get("metadata", {}),
            "similarity_score": float(ctx.get("similarity_score", 0.0))
        }
        serializable_contexts.append(serializable_ctx)
    
    return {
        "answer": answer,
        "contexts": serializable_contexts,
        "contexts_used": len(contexts),
        "model": deployment
    }