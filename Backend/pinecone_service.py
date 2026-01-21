# backend/pinecone_service.py
import numpy as np
from typing import List, Dict, Any, Optional
import json
import hashlib
from datetime import datetime

class PineconeService:
    """Mock Pinecone service for demo - replace with real Pinecone for production"""
    
    def __init__(self):
        self.vectors = {}
        self.metadata_store = {}
        print("🧠 Mock Pinecone service initialized")
    
    def embed_text(self, text: str, embedder) -> List[float]:
        """Generate embedding using provided embedder"""
        return embedder.encode(text).tolist()
    
    def store_knowledge(self, text: str, metadata: Dict[str, Any], embedder) -> str:
        """Store text with metadata"""
        # Generate ID
        doc_id = hashlib.md5(text.encode()).hexdigest()[:16]
        
        # Generate embedding
        embedding = self.embed_text(text, embedder)
        
        # Store
        self.vectors[doc_id] = {
            "embedding": embedding,
            "text": text,
            "metadata": {
                **metadata,
                "stored_at": datetime.now().isoformat(),
                "doc_id": doc_id
            }
        }
        
        # Also index by metadata
        category = metadata.get("category", "general")
        if category not in self.metadata_store:
            self.metadata_store[category] = []
        self.metadata_store[category].append(doc_id)
        
        return doc_id
    
    def search_similar(self, query_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """Search for similar vectors (cosine similarity)"""
        results = []
        
        for doc_id, data in self.vectors.items():
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, data["embedding"])
            
            results.append({
                "id": doc_id,
                "score": similarity,
                "metadata": data["metadata"],
                "text": data["text"]
            })
        
        # Sort by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a_np = np.array(a)
        b_np = np.array(b)
        return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    
    def get_by_category(self, category: str) -> List[Dict]:
        """Get all documents in a category"""
        doc_ids = self.metadata_store.get(category, [])
        return [self.vectors[doc_id] for doc_id in doc_ids if doc_id in self.vectors]
    
    def delete_all(self):
        """Clear all vectors"""
        self.vectors.clear()
        self.metadata_store.clear()
    
    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            "total_documents": len(self.vectors),
            "categories": list(self.metadata_store.keys()),
            "documents_per_category": {
                cat: len(docs) for cat, docs in self.metadata_store.items()
            }
        }

# For real Pinecone (uncomment and configure if you have Pinecone API key)
"""
import pinecone
from dotenv import load_dotenv
import os

load_dotenv()

class RealPineconeService:
    def __init__(self):
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )
        
        index_name = "jarvis-knowledge"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=384,
                metric="cosine"
            )
        
        self.index = pinecone.Index(index_name)
    
    def store_knowledge(self, text: str, metadata: dict, embedder):
        embedding = embedder.encode(text).tolist()
        doc_id = hashlib.md5(text.encode()).hexdigest()[:16]
        
        self.index.upsert(vectors=[{
            "id": doc_id,
            "values": embedding,
            "metadata": {**metadata, "text": text}
        }])
        
        return doc_id
    
    def search_similar(self, query_embedding: list, top_k=3):
        return self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        ).matches
"""