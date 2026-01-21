# backend/app.py (COMPLETE VERSION WITH FIXES)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import json

# Import our modules
from model_manager import DistilBERTManager
from pinecone_service import PineconeService
from knowledge_base import KnowledgeBase
from llm_manager import SmartLLMManager

# Initialize FastAPI app
app = FastAPI(
    title="Jarvis Enterprise API",
    description="AI Assistant for GRC with Ollama & DistilBERT fallback",
    version="2.0.0"
)

# Fix Pydantic warning
from pydantic import ConfigDict

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
print("🚀 Initializing Jarvis Enterprise Assistant v2.0...")

# Initialize Pinecone and Knowledge Base
pinecone_service = PineconeService()
embedder = DistilBERTManager().embedder
knowledge_base = KnowledgeBase(pinecone_service, embedder)
knowledge_base.initialize()

# Initialize Smart LLM Manager
llm_manager = SmartLLMManager(
    use_ollama=True,
    ollama_model="mistral"
)

print(f"🎯 Active AI Backend: {llm_manager.llm_choice}")

# Pydantic models with config to fix warning
class QueryRequest(BaseModel):
    message: str
    user_id: Optional[str] = "enterprise_user"
    force_backend: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())
    message: str
    user_id: Optional[str] = "enterprise_user"
    force_backend: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())
    message: str
    user_id: Optional[str] = "enterprise_user"
    force_backend: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())

class QueryResponse(BaseModel):
    response: str
    sources: List[str]
    category: str
    backend: str
    model: str
    response_time: float
    fallback_used: bool
    tokens_used: int
    timestamp: str
    
    model_config = ConfigDict(protected_namespaces=())

class LLMSwitchRequest(BaseModel):
    backend: str
    model_name: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())

class KnowledgeRequest(BaseModel):
    text: str
    category: str = "general"
    tags: List[str] = []
    
    model_config = ConfigDict(protected_namespaces=())

# API Endpoints
@app.get("/")
async def root():
    return {
        "service": "Jarvis Enterprise API v2.0",
        "status": "operational",
        "version": "2.0.0",
        "ai_backends": ["ollama", "distilbert"],
        "active_backend": llm_manager.llm_choice,
        "endpoints": [
            "/query - Ask questions",
            "/llm/status - LLM system status",
            "/llm/switch - Switch AI backend",
            "/knowledge - Add knowledge",
            "/search - Search knowledge base",
            "/stats - System statistics",
            "/health - Health check"
        ]
    }

@app.get("/health")
async def health_check():
    llm_status = llm_manager.get_status()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "llm": f"{llm_manager.llm_choice}",
            "knowledge_base": "ready",
            "vector_store": "operational"
        },
        "llm_details": {
            "primary_backend": llm_manager.llm_choice,
            "ollama_available": llm_status["ollama_available"],
            "distilbert_available": True
        }
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # Get knowledge base stats
        kb_stats = knowledge_base.get_stats()
        
        # Get LLM stats
        llm_status = llm_manager.get_status()
        
        return {
            "knowledge_base": kb_stats,
            "llm_system": {
                "current_backend": llm_manager.llm_choice,
                "ollama_available": llm_status["ollama_available"],
                "query_stats": llm_status.get("stats", {})
            },
            "system": {
                "uptime": "running",
                "models_loaded": True,
                "knowledge_items": kb_stats.get("total_documents", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

@app.get("/llm/status")
async def get_llm_status():
    """Get detailed LLM status and statistics"""
    status = llm_manager.get_status()
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "recommendation": "Use Ollama for better quality responses" if status["ollama_available"] else "Using DistilBERT (Ollama not available)"
    }

@app.post("/llm/switch")
async def switch_llm_backend(request: LLMSwitchRequest):
    """Switch between Ollama and DistilBERT backends"""
    
    if request.backend.lower() == "ollama":
        success = llm_manager.switch_to_ollama(request.model_name)
        
        if success:
            return {
                "success": True,
                "message": f"Switched to Ollama with model: {llm_manager.ollama_model}",
                "backend": "ollama"
            }
        else:
            return {
                "success": False,
                "message": "Ollama not available. Check if Ollama is running.",
                "backend": "distilbert"
            }
    
    elif request.backend.lower() == "distilbert":
        llm_manager.switch_to_distilbert()
        return {
            "success": True,
            "message": "Switched to DistilBERT",
            "backend": "distilbert"
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid backend. Use 'ollama' or 'distilbert'"
        )

@app.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest):
    try:
        # Handle force backend if specified
        if request.force_backend:
            if request.force_backend == "ollama":
                llm_manager.switch_to_ollama()
            elif request.force_backend == "distilbert":
                llm_manager.switch_to_distilbert()
        
        # 1. Classify the query
        classification = llm_manager.classify_query(request.message)
        
        # 2. Search for relevant context
        search_results = knowledge_base.search(request.message, top_k=3)
        
        # 3. Prepare context from search results
        context_chunks = []
        sources = []
        
        for result in search_results:
            if result["score"] > 0.3:  # Only use relevant results
                context_chunks.append(result["text"])
                sources.append(f"{result['category']} ({result['score']:.2f})")
        
        context = "\n\n".join(context_chunks) if context_chunks else "General enterprise knowledge."
        
        # 4. Generate response using smart LLM manager
        llm_result = llm_manager.generate_response(
            query=request.message,
            context=context,
            category=classification["primary_category"]
        )
        
        # 5. Format sources
        if not sources:
            sources = ["General knowledge base"]
        
        return QueryResponse(
            response=llm_result["response"],
            sources=sources[:3],
            category=classification["primary_category"],
            backend=llm_result["backend"],
            model=llm_result["model"],
            response_time=llm_result["response_time"],
            fallback_used=llm_result["fallback_used"],
            tokens_used=llm_result.get("tokens_used", 0),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.post("/knowledge")
async def add_knowledge(request: KnowledgeRequest):
    try:
        result = knowledge_base.add_knowledge(
            text=request.text,
            category=request.category,
            source="api",
            tags=request.tags
        )
        
        return {
            "success": True,
            "message": "Knowledge added successfully",
            "doc_id": result["doc_id"],
            "category": request.category
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding knowledge: {str(e)}"
        )

@app.get("/search/{query}")
async def search_knowledge(query: str, limit: int = 5):
    results = knowledge_base.search(query, top_k=limit)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

@app.post("/feedback")
async def submit_feedback(query: str, response: str, rating: int, feedback: Optional[str] = None):
    # In production, store in database
    print(f"📝 Feedback received: {rating}/5 - {feedback}")
    return {
        "thank_you": True,
        "message": "Feedback recorded for model improvement",
        "rating": rating
    }

@app.get("/categories")
async def list_categories():
    stats = knowledge_base.get_stats()
    return {
        "categories": stats.get("categories", []),
        "counts": stats.get("documents_per_category", {})
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 Jarvis Enterprise Assistant v2.0")
    print("📡 API Server starting on http://localhost:8000")
    print("🎯 Primary AI: Ollama (with DistilBERT fallback)")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )