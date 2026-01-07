from re import S
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DocumentMetadata(BaseModel):
    document_id: Optional[str] = None  # Make it optional with default None
    title: str
    document_type: str #topic of the chatbot recognition
    version: str
    approved: bool
    approved_by: str
    approval_date: datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp:Optional[datetime]=None

class ChatSession(BaseModel):
    session_id:str
    messages: List[ChatMessage]=[]
    selected_topic: Optional[str]= None
    created_at: datetime
    updated_at:datetime

class ChatRequest(BaseModel):
    session_id: Optional[str]= None
    message:str
    topic: Optional[str]=None 

class ChatResponse(BaseModel):
    session_id:str
    message:str
    topic: Optional[str]
    sources: List[dict]=[]
    available_topics: List[str]=[]



    