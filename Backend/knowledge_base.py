# backend/knowledge_base.py
import json
from datetime import datetime
from typing import List, Dict, Any

class KnowledgeBase:
    """Manages enterprise knowledge storage and retrieval"""
    
    def __init__(self, pinecone_service, embedder):
        self.pinecone = pinecone_service
        self.embedder = embedder
        
        # Pre-loaded enterprise knowledge
        self.initial_knowledge = [
            {
                "text": "Diligent is the leading GRC SaaS company serving 1M+ users across 25,000 organizations worldwide with governance, risk, and compliance solutions.",
                "category": "company",
                "source": "company_overview",
                "tags": ["diligent", "grc", "enterprise"]
            },
            {
                "text": "Effective board governance requires quarterly meetings, annual evaluations, secure document management, and clear committee structures with defined responsibilities.",
                "category": "governance",
                "source": "best_practices",
                "tags": ["board", "governance", "meetings"]
            },
            {
                "text": "SOX compliance mandates internal controls over financial reporting, CEO/CFO certifications, audit trails, and regular independent audits.",
                "category": "compliance",
                "source": "regulations",
                "tags": ["sox", "compliance", "audit"]
            },
            {
                "text": "Enterprise Risk Management (ERM) framework includes risk identification, assessment, mitigation planning, monitoring, and reporting to stakeholders.",
                "category": "risk",
                "source": "framework",
                "tags": ["erm", "risk", "management"]
            },
            {
                "text": "Modern board portals should feature secure document distribution, electronic signatures, meeting scheduling, voting tools, and compliance tracking capabilities.",
                "category": "technology",
                "source": "product_features",
                "tags": ["board_portal", "features", "technology"]
            },
            {
                "text": "GDPR compliance requires data protection impact assessments, breach notification within 72 hours, data minimization, and privacy by design principles.",
                "category": "compliance",
                "source": "regulations",
                "tags": ["gdpr", "privacy", "data_protection"]
            },
            {
                "text": "Risk assessment involves identifying potential threats, analyzing their likelihood and impact, and prioritizing mitigation efforts based on risk appetite.",
                "category": "risk",
                "source": "process",
                "tags": ["risk_assessment", "methodology"]
            }
        ]
    
    def initialize(self):
        """Seed the knowledge base with initial data"""
        print("📚 Initializing knowledge base...")
        
        for i, knowledge in enumerate(self.initial_knowledge):
            doc_id = self.pinecone.store_knowledge(
                text=knowledge["text"],
                metadata={
                    "category": knowledge["category"],
                    "source": knowledge["source"],
                    "tags": json.dumps(knowledge["tags"]),
                    "added_at": datetime.now().isoformat()
                },
                embedder=self.embedder
            )
            print(f"  ✓ Added: {knowledge['category']} (ID: {doc_id})")
        
        print(f"✅ Knowledge base initialized with {len(self.initial_knowledge)} items")
    
    def add_knowledge(self, text: str, category: str = "general", source: str = "user", tags: List[str] = None):
        """Add new knowledge to the base"""
        doc_id = self.pinecone.store_knowledge(
            text=text,
            metadata={
                "category": category,
                "source": source,
                "tags": json.dumps(tags or []),
                "added_at": datetime.now().isoformat()
            },
            embedder=self.embedder
        )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Knowledge added successfully"
        }
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant knowledge"""
        query_embedding = self.embedder.encode(query).tolist()
        results = self.pinecone.search_similar(query_embedding, top_k=top_k)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.get("text", ""),
                "category": result.get("metadata", {}).get("category", "unknown"),
                "source": result.get("metadata", {}).get("source", "unknown"),
                "score": round(result.get("score", 0), 3),
                "doc_id": result.get("metadata", {}).get("doc_id", "")
            })
        
        return formatted_results
    
    def get_by_category(self, category: str) -> List[Dict]:
        """Get all knowledge in a category"""
        return self.pinecone.get_by_category(category)
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return self.pinecone.get_stats()