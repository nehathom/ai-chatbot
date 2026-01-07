import uuid 
from datetime import datetime
from typing import  Dict,Optional,List
from pathlib import Path
import json

from app.models.schemas import ChatSession,ChatMessage
from app.utils.logger import get_logger

logger=get_logger(__name__)

class SessionManager:
    """Manage chat sessions and conversation history."""

    def __init__(self):
        self.sessions:Dict[str,ChatSession]={}
        self.sessions_dir=Path("data/sessions")
        self.sessions_dir.mkdir(parents=True,exist_ok=True)

    def create_session(self)->str:
        """Create a new chat session."""
        session_id=str(uuid.uuid4())
        session=ChatSession(  # Fixed typo
            session_id=session_id,
            messages=[],
            selected_topic=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.sessions[session_id]=session  
        logger.info(f"Created new chat session: {session_id}")
        return session_id
    def get_session(self,session_id:str)-> Optional[ChatSession]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    def add_message(self,session_id:str,role:str,content:str):
        """Add a message to the conversation history."""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return 
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        session.messages.append(message)
        session.updated_at=datetime.utcnow()
        logger.info(f"Added{role} message to session {session_id}")

    def set_topic(self, session_id:str,topic:str):
        """Set the topic for a session."""
        session=self.sessions.get(session_id)
        if session:
            session.selected_topic=topic 
            logger.info(f"Set topic '{topic}' for session {session_id} ")
    
    def get_conversation_history(self,session_id:str,max_messages:int=10)-> List[dict]:
        """Get recent conversation history."""
        session= self.sessions.get(session_id)
        if not session:
            return []
        
        recent_messages=session.messages[-max_messages:]
        return [
            {"role":msg.role,"content":msg.content}
            for msg in recent_messages
        ]
    def save_session(self,session_id:str):
        """Save session to disk."""
        session=self.sessions.get(session_id)
        if not session:
            return 
        
        file_path=self.sessions_dir/f"{session_id}.json"
        with open(file_path,"w") as f:
            json.dump(session.model_dump(),f,indent=2,default=str)
        logger.info(f"Saved session {session_id} to disk")

session_manager=SessionManager()