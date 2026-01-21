# backend/model_manager.py
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DistilBERTManager:
    """Manager for DistilBERT models - Lightweight and fast"""
    
    def __init__(self):
        logger.info("Loading DistilBERT models...")
        
        # For text embeddings (384-dimensional)
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("✓ Embedding model loaded")
        
        # For question answering
        self.qa_model = pipeline(
            "question-answering",
            model="distilbert-base-uncased-distilled-squad",
            tokenizer="distilbert-base-uncased-distilled-squad",
            device=-1  # CPU (use 0 for GPU if available)
        )
        logger.info("✓ QA model loaded")
        
        # For text generation (small GPT-2 for demo)
        self.generator = pipeline(
            "text-generation",
            model="distilgpt2",
            max_length=200,
            device=-1
        )
        logger.info("✓ Text generation model loaded")
        
        # Enterprise knowledge patterns
        self.knowledge_patterns = {
            "governance": [
                "board management", "director oversight", "meeting minutes",
                "committee structure", "corporate governance", "board evaluation"
            ],
            "risk": [
                "risk assessment", "mitigation strategy", "risk appetite",
                "enterprise risk", "risk monitoring", "risk reporting"
            ],
            "compliance": [
                "regulatory compliance", "SOX requirements", "GDPR",
                "audit trail", "policy management", "compliance reporting"
            ],
            "diligent": [
                "GRC platform", "board portal", "risk management software",
                "compliance solution", "Diligent products", "enterprise governance"
            ]
        }
        
        logger.info("✓ Model manager initialized successfully")
    
    def embed_text(self, text: str):
        """Generate embeddings for text"""
        return self.embedder.encode(text)
    
    def answer_question(self, context: str, question: str) -> str:
        """Answer question based on context"""
        try:
            result = self.qa_model(question=question, context=context[:2000])
            return result['answer']
        except Exception as e:
            logger.error(f"QA error: {e}")
            return "Unable to generate answer from context."
    
    def generate_response(self, query: str, context: str = None) -> str:
        """Generate enterprise-focused response"""
        
        # Classify query type
        query_lower = query.lower()
        category = "general"
        
        for cat, patterns in self.knowledge_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                category = cat
                break
        
        # Base prompts for different categories
        prompts = {
            "governance": f"As a governance expert at Diligent, I recommend: ",
            "risk": f"For enterprise risk management, best practices include: ",
            "compliance": f"Compliance requirements typically involve: ",
            "diligent": f"Diligent's GRC solutions provide: ",
            "general": f"Based on enterprise best practices: "
        }
        
        # If context is provided, use QA model
        if context:
            answer = self.answer_question(context, query)
            return f"{prompts[category]}{answer}"
        
        # Otherwise, use text generation with enterprise focus
        enterprise_prompt = f"""You are Jarvis, an enterprise AI assistant for Diligent.
Query: {query}
Category: {category}

Provide a concise, professional response:"""
        
        try:
            result = self.generator(
                enterprise_prompt,
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )
            return result[0]['generated_text'].split("Provide a concise, professional response:")[-1].strip()
        except:
            # Fallback response
            return f"{prompts[category]}implementing robust processes and using technology solutions like Diligent's platform."
    
    def classify_query(self, query: str) -> dict:
        """Classify the query into enterprise categories"""
        query_lower = query.lower()
        scores = {}
        
        for category, patterns in self.knowledge_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            scores[category] = score
        
        primary_category = max(scores, key=scores.get) if any(scores.values()) else "general"
        
        return {
            "primary_category": primary_category,
            "confidence": scores[primary_category] / len(self.knowledge_patterns[primary_category]) if primary_category != "general" else 0,
            "all_categories": scores
        }