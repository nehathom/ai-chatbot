from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.ingestion.loader import ingest_document
from app.models.schemas import DocumentMetadata, ChatRequest, ChatResponse  # Add ChatRequest, ChatResponse
from app.indexing.indexer import build_index, search_index
from app.rag.retriever import retrieve_context
from app.rag.generator import generate_answer
from app.chat.chatbot import chat, get_available_topics
from app.chat.session_manager import session_manager
from app.utils.logger import get_logger
from datetime import datetime
from typing import Optional

logger = get_logger(__name__)

app = FastAPI(
    title="AI-Powered Knowledge Framework",
    description="Enterprise RAG system with governance controls",
    version="3.0.0",
)

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI-Powered Knowledge Framework")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI-Powered Knowledge Framework")


@app.get("/chat/topics")
async def get_topics():
    """Get list of available topics from the knowledge base."""
    logger.info("Topics requested")
    try:
        topics = get_available_topics()
        return {
            "status": "success",
            "topics": topics,
            "count": len(topics)
        }
    except Exception as e:
        logger.error(f"Failed to get topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/session")
async def create_chat_session():
    """Create a new chat session."""
    session_id = session_manager.create_session()
    topics = get_available_topics()
    
    return {
        "status": "success",
        "session_id": session_id,
        "available_topics": topics,
        "message": "Welcome! Please select a topic or ask me anything."
    }

@app.post("/chat/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """
    Send a message to the chatbot.
    
    The chatbot will:
    1. Use selected topic to filter documents
    2. Retrieve relevant context using RAG
    3. Generate a response with conversation history
    4. Return answer with sources
    """
    logger.info(f"Chat message received - Session: {request.session_id}, Topic: {request.topic}")
    
    try:
        # Create session if not provided
        if not request.session_id:
            request.session_id = session_manager.create_session()
        
        # Process the chat message
        response = chat(
            session_id=request.session_id,
            user_message=request.message,
            topic=request.topic
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session."""
    history = session_manager.get_conversation_history(session_id, max_messages=20)
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "status": "success",
        "session_id": session_id,
        "selected_topic": session.selected_topic,
        "messages": history,
        "message_count": len(history)
    }

@app.get("/chat/ui", response_class=HTMLResponse)
async def chat_ui():
    """Serve an enhanced chat UI with file upload."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Knowledge Assistant</title>
        <link
      href="https://fonts.googleapis.com/css2?family=Afacad:ital,wght@0,400..700;1,400..700&display=swap"
      rel="stylesheet"
        />

        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Afacad', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                letter-spacing: 0.2px;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .chat-container {
                width: 90%;
                max-width: 800px;
                height: 90vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .chat-header {
                background: linear-gradient(120deg, #1b2540 0%, #2c3e5c 50%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .chat-header h1 {
                font-size: 24px;
                margin-bottom: 10px;
            }
            .controls {
                padding: 15px;
                background: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            .controls select, .controls input[type="text"] {
                flex: 1;
                padding: 10px;
                border: 2px solid #667eea;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            .upload-section {
                padding: 15px;
                background: #fff9e6;
                border-bottom: 2px solid #ffd700;
                display: flex;
                gap: 10px;
                align-items: center;
            }
            .file-input-wrapper {
                position: relative;
                overflow: hidden;
                display: inline-block;
            }
            .file-input-wrapper input[type=file] {
                position: absolute;
                left: -9999px;
            }
            .file-input-wrapper label {
                display: inline-block;
                padding: 10px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .file-input-wrapper label:hover {
                transform: scale(1.05);
            }
            .file-name {
                flex: 1;
                color: #666;
                font-size: 14px;
            }
            .upload-btn {
                padding: 10px 20px;
                background: #14b8a6;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .upload-btn:hover {
                transform: scale(1.05);
            }
            .upload-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .message {
                margin-bottom: 15px;
                display: flex;
                animation: fadeIn 0.3s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .message.user {
                justify-content: flex-end;
            }
            .message.system {
                justify-content: center;
            }
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
            }
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .message.assistant .message-content {
                background: white;
                color: #333;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .message.system .message-content {
                background: #fff9e6;
                color: #856404;
                border: 1px solid #ffd700;
                text-align: center;
                max-width: 90%;
            }
            .sources {
                font-size: 11px;
                color: #666;
                margin-top: 8px;
                padding-top: 8px;
                border-top: 1px solid #e0e0e0;
            }
            .chat-input {
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            .chat-input input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            .chat-input input:focus {
                border-color: #667eea;
            }
            .chat-input button {
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .chat-input button:hover {
                transform: scale(1.05);
            }
            .chat-input button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .loading {
                display: none;
                text-align: center;
                color: #666;
                font-style: italic;
                padding: 10px;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h1> AI KNOWLEDGE ASSISTANT</h1>
                <p>Upload documents and ask questions!</p>
            </div>
            
            <div class="upload-section">
                <div class="file-input-wrapper">
                    <input type="file" id="fileInput" accept=".pdf,.docx" onchange="handleFileSelect(event)">
                    <label for="fileInput">📄 Choose File</label>
                </div>
                <span class="file-name" id="fileName">No file selected</span>
                <input type="text" id="docTitle" placeholder="Document title (optional)" style="width: 200px;">
                <button class="upload-btn" id="uploadBtn" onclick="uploadDocument()" disabled>Upload</button>
            </div>
            
            <div class="controls">
                <select id="topicSelect">
                    <option value="">All Topics</option>
                </select>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    <div class="message-content">
                        👋 Hello! I'm your AI Knowledge Assistant. 
                        <br><br>
                        📤 <b>Upload a document</b> above to add it to my knowledge base
                        <br>
                        💬 <b>Ask me anything</b> about the documents I have access to
                        <br><br>
                        Select a topic or just start chatting!
                    </div>
                </div>
            </div>
            
            <div class="loading" id="loading">AI is thinking...</div>
            
            <div class="chat-input">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="Type your message..." 
                    onkeypress="if(event.key==='Enter') sendMessage()"
                />
                <button onclick="sendMessage()" id="sendBtn">Send</button>
            </div>
        </div>

        <script>
            let sessionId = null;
            let selectedFile = null;
            const API_URL = 'http://127.0.0.1:8000';

            // Initialize
            async function init() {
                // Create session
                const sessionRes = await fetch(`${API_URL}/chat/session`, { method: 'POST' });
                const sessionData = await sessionRes.json();
                sessionId = sessionData.session_id;
                
                // Load topics
                await loadTopics();
            }

            async function loadTopics() {
                const topicsRes = await fetch(`${API_URL}/chat/topics`);
                const topicsData = await topicsRes.json();
                
                const select = document.getElementById('topicSelect');
                select.innerHTML = '<option value="">All Topics</option>';
                topicsData.topics.forEach(topic => {
                    const option = document.createElement('option');
                    option.value = topic;
                    option.textContent = topic;
                    select.appendChild(option);
                });
            }

            function handleFileSelect(event) {
                selectedFile = event.target.files[0];
                const fileName = document.getElementById('fileName');
                const uploadBtn = document.getElementById('uploadBtn');
                
                if (selectedFile) {
                    fileName.textContent = selectedFile.name;
                    uploadBtn.disabled = false;
                } else {
                    fileName.textContent = 'No file selected';
                    uploadBtn.disabled = true;
                }
            }

            async function uploadDocument() {
                if (!selectedFile) return;
                
                const uploadBtn = document.getElementById('uploadBtn');
                const docTitle = document.getElementById('docTitle').value || selectedFile.name;
                
                uploadBtn.disabled = true;
                uploadBtn.textContent = 'Uploading...';
                
                addMessage('system', `📤 Uploading "${docTitle}"...`);
                
                try {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    
                    const response = await fetch(
                        `${API_URL}/documents/upload-and-index?title=${encodeURIComponent(docTitle)}&document_type=General&approved=true&approved_by=chat_user`,
                        {
                            method: 'POST',
                            body: formData
                        }
                    );
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        addMessage('system', `✅ "${docTitle}" uploaded and indexed! You can now ask questions about it.`);
                        
                        // Reload topics
                        await loadTopics();
                        
                        // Clear file input
                        document.getElementById('fileInput').value = '';
                        document.getElementById('fileName').textContent = 'No file selected';
                        document.getElementById('docTitle').value = '';
                        selectedFile = null;
                    } else {
                        addMessage('system', `❌ Upload failed: ${data.detail}`);
                    }
                    
                } catch (error) {
                    addMessage('system', '❌ Upload failed. Please try again.');
                    console.error(error);
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            }

            function addMessage(role, content, sources = []) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                
                let sourcesHTML = '';
                if (sources && sources.length > 0) {
                    sourcesHTML = '<div class="sources"> Sources: ' + 
                        sources.map(s => s.document_title).join(', ') + 
                        '</div>';
                }
                
                messageDiv.innerHTML = `
                    <div class="message-content">
                        ${content}
                        ${sourcesHTML}
                    </div>
                `;
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                const topic = document.getElementById('topicSelect').value;
                const sendBtn = document.getElementById('sendBtn');
                const loading = document.getElementById('loading');
                
                // Disable input
                input.disabled = true;
                sendBtn.disabled = true;
                loading.style.display = 'block';
                
                // Add user message
                addMessage('user', message);
                input.value = '';
                
                try {
                    // Send to API
                    const response = await fetch(`${API_URL}/chat/message`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: sessionId,
                            message: message,
                            topic: topic || null
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Add assistant response
                    addMessage('assistant', data.message, data.sources);
                    
                } catch (error) {
                    addMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
                    console.error(error);
                } finally {
                    input.disabled = false;
                    sendBtn.disabled = false;
                    loading.style.display = 'none';
                    input.focus();
                }
            }

            // Initialize on load
            init();
        </script>
    </body>
    </html>
    """

@app.post("/documents/upload-and-index")
async def upload_and_index_document(
    file: UploadFile = File(...),
    title: str = "Untitled",
    document_type: str = "General",
    version: str = "1.0",
    approved: bool = True,  # Default to approved for chat uploads
    approved_by: str = "chatbot_user",
):
    """Upload a document and immediately add it to the index."""
    logger.info(f"Upload + Index request: {file.filename}")
    
    try: 
        # Step 1: Upload document
        metadata = DocumentMetadata(
            title=title,
            document_type=document_type,
            version=version,
            approved=approved,
            approved_by=approved_by,
            approval_date=datetime.utcnow()
        )
        upload_result = ingest_document(file, metadata)
        logger.info(f"Document uploaded: {upload_result['document_id']}")
        
        # Step 2: Rebuild index to include new document
        logger.info("Rebuilding index with new document...")
        store = build_index(approved_only=True)
        stats = store.get_stats()
        logger.info(f"Index rebuilt: {stats}")
        
        return {
            "status": "success",
            "message": f"Document '{title}' uploaded and indexed successfully!",
            "data": upload_result,
            "index_stats": stats
        }
    except Exception as e:
        logger.error(f"Upload + Index failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"status": "running", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"message": "OK", "timestamp": datetime.utcnow().isoformat()}

@app.post("/documents/upload")
async def upload_documents(
    file: UploadFile = File(...),
    title: str = "Untitled",
    document_type: str = "General",
    version: str = "1.0",
    approved: bool = False,
    approved_by: str = "",
):
    logger.info(f"Upload request: {file.filename} (approved={approved})")
    
    try: 
        metadata = DocumentMetadata(
            title=title,
            document_type=document_type,
            version=version,
            approved=approved,
            approved_by=approved_by,
            approval_date=datetime.utcnow()
        )
        result = ingest_document(file, metadata)
        logger.info(f"Document uploaded successfully: {result['document_id']}")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/index/build")
async def build_vector_index(
    approved_only: bool = Query(True, description="Only index approved documents"),
    document_type: Optional[str] = Query(None, description="Filter by document type")
):
    """Build or rebuild the vector index with governance controls."""
    logger.info(f"Index build requested (approved_only={approved_only}, document_type={document_type})")
    
    try:
        store = build_index(approved_only=approved_only, document_type=document_type)
        stats = store.get_stats()
        logger.info(f"Index built successfully: {stats}")
        return {
            "status": "success",
            "message": "Vector index built successfully",
            "stats": stats,
            "governance": {
                "approved_only": approved_only,
                "document_type_filter": document_type
            }
        }
    except Exception as e:
        logger.error(f"Index build failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(
    query: str,
    top_k: int = 5,
    document_type: Optional[str] = Query(None, description="Filter by document type")
):
    """Search the vector index with optional filtering."""
    logger.info(f"Search request: '{query}' (top_k={top_k}, document_type={document_type})")
    
    try:
        results = search_index(query, k=top_k, document_type=document_type)
        return {
            "status": "success",
            "query": query,
            "results": results,
            "filters": {"document_type": document_type}
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_knowledge(
    query: str,
    top_k: int = 3,
    document_type: Optional[str] = Query(None, description="Filter by document type")
):
    """
    RAG endpoint with governance - Retrieve context and generate answer.
    
    Args:
        query: User's question
        top_k: Number of context chunks to retrieve
        document_type: Filter by document type for compliance
    """
    logger.info(f"Query request: '{query}' (top_k={top_k}, document_type={document_type})")
    
    try:
        # Step 1: Retrieve relevant contexts with filtering
        contexts = retrieve_context(query, k=top_k, document_type=document_type)
        
        if not contexts:
            logger.warning("No relevant documents found")
            return {
                "status": "success",
                "query": query,
                "answer": "No relevant documents found in the knowledge base.",
                "contexts": []
            }
        
        # Step 2: Generate answer using GPT
        result = generate_answer(query, contexts)
        
        logger.info("Query completed successfully")
        
        # Step 3: Return complete response
        return {
            "status": "success",
            "query": query,
            "answer": result["answer"],
            "contexts": result["contexts"],
            "metadata": {
                "contexts_used": result["contexts_used"],
                "model": result["model"],
                "document_type_filter": document_type
            }
        }
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))