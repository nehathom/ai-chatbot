import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

from app.rag.retriever import retrieve_context
from app.chat.session_manager import session_manager
from app.models.schemas import ChatSession
from app.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_available_topics() -> List[str]:
    """Get list of available document topics from the knowledge base."""
    from pathlib import Path
    import json

    topics = set()
    chunks_dir = Path("data/chunks")

    for chunk_file in chunks_dir.glob("*.json"):
        with open(chunk_file, "r") as f:
            chunks = json.load(f)
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                if metadata.get("approved", False):
                    doc_type = metadata.get("document_type")
                    if doc_type:
                        topics.add(doc_type)
    
    logger.info(f"Available topics: {sorted(topics)}")
    return sorted(topics)

def build_chat_prompt(
    user_message: str,
    contexts: List[Dict],
    conversation_history: List[Dict],
    topic: Optional[str] = None
) -> List[Dict]:
    """Build chat prompt with context and history."""

    # System message
    system_message = """You are a helpful AI assistant with access to a knowledge base of approved documents. Your role is to answer questions accurately based on the provided context.

Guidelines:
- Answer concisely and accurately based on the context
- If you don't have enough information, say so
- Reference specific documents when relevant
- Maintain a friendly, professional tone
- Build on previous conversation context when appropriate"""

    if topic:
        system_message += f"\n\nCurrent topic filter: {topic} documents only."

    if contexts:
        context_str = "\n\n".join([
            f"[Source {i+1}]\n{ctx['text']}"
            for i, ctx in enumerate(contexts)
        ])
        system_message += f"\n\nRelevant Context:\n{context_str}"

    # Build message array
    messages = [{"role": "system", "content": system_message}]

    # Add conversation history (last 10 messages)
    messages.extend(conversation_history[-10:])  # Fixed: extend not exten

    messages.append({"role": "user", "content": user_message})

    return messages 

def chat(
    session_id: str,
    user_message: str,
    topic: Optional[str] = None,
    k: int = 3
) -> Dict:
    """
    Process a chat message with RAG.

    Args:
        session_id: Chat session ID
        user_message: User's message
        topic: Optional topic filter
        k: Number of context chunks to retrieve
    
    Returns:
        Response dictionary with answer and metadata
    """

    logger.info(f"Chat request - Session: {session_id}, Topic: {topic}, Message: '{user_message[:50]}...'")

    # Get or create session
    session = session_manager.get_session(session_id)
    if not session:
        logger.info(f"Session not found, creating new: {session_id}")
        new_session = ChatSession(
            session_id=session_id,
            messages=[],
            selected_topic=topic,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session_manager.sessions[session_id] = new_session
        session = new_session
    
    # Update topic if provided
    if topic:
        session_manager.set_topic(session_id, topic)
    else:
        topic = session.selected_topic

    # Retrieve relevant context
    contexts = []
    if user_message.lower() not in ["hello", "hi", "help", "topics"]:
        try:
            contexts = retrieve_context(user_message, k=k, document_type=topic)
            logger.info(f"Retrieved {len(contexts)} context chunks")
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
    
    # Get conversation history
    conversation_history = session_manager.get_conversation_history(session_id)
    
    # Build chat messages
    messages = build_chat_prompt(user_message, contexts, conversation_history, topic)

    # Call GPT
    logger.info("Calling Azure OpenAI for chat completion")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.7,
        max_tokens=800
    )

    assistant_message = response.choices[0].message.content  # Fixed: choices not choice
    logger.info(f"Generated response ({len(assistant_message)} chars)")

    # Save messages to session
    session_manager.add_message(session_id, "user", user_message)
    session_manager.add_message(session_id, "assistant", assistant_message)

    # Prepare sources
    sources = [
        {
            "chunk_id": ctx.get("chunk_id"),
            "document_title": ctx.get("metadata", {}).get("title", "Unknown"),
            "document_type": ctx.get("metadata", {}).get("document_type"),  # Fixed: removed extra f
            "similarity_score": float(ctx.get("similarity_score", 0))
        }
        for ctx in contexts
    ]

    return {
        "session_id": session_id,
        "message": assistant_message,
        "topic": topic,
        "sources": sources,
        "available_topics": get_available_topics()
    }




