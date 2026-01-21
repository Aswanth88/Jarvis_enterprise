# backend/llm_manager.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import both managers
from model_manager import DistilBERTManager
from ollama_manager import OllamaManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartLLMManager:
    """Intelligent LLM manager that tries Ollama first, falls back to DistilBERT"""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = "mistral"):
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.llm_choice = "unknown"
        self.stats = {
            "total_queries": 0,
            "ollama_success": 0,
            "ollama_failures": 0,
            "fallback_used": 0
        }
        
        # Initialize managers
        logger.info("🤖 Initializing AI managers...")
        
        # Initialize DistilBERT (always available)
        self.distilbert = DistilBERTManager()
        logger.info("✅ DistilBERT manager initialized")
        
        # Initialize Ollama (might not be available)
        self.ollama = None
        if self.use_ollama:
            try:
                self.ollama = OllamaManager(model=ollama_model)
                if self.ollama.available:
                    logger.info("✅ Ollama manager initialized")
                    self.llm_choice = "ollama"
                else:
                    logger.warning("⚠️ Ollama not available, using DistilBERT")
                    self.llm_choice = "distilbert"
            except Exception as e:
                logger.error(f"❌ Failed to initialize Ollama: {e}")
                self.llm_choice = "distilbert"
        else:
            self.llm_choice = "distilbert"
        
        logger.info(f"🎯 Primary LLM: {self.llm_choice}")
    
    def generate_response(self, query: str, context: str = "", 
                         category: str = "general") -> Dict[str, Any]:
        """Generate response with intelligent fallback"""
        
        self.stats["total_queries"] += 1
        start_time = datetime.now()
        
        # Try Ollama first if available and enabled
        if self.ollama and self.ollama.available and self.use_ollama:
            logger.info(f"🔄 Trying Ollama for query: {query[:50]}...")
            
            # Custom system prompt based on category
            system_prompt = self._get_system_prompt(category)
            
            ollama_result = self.ollama.generate_response(
                query=query,
                context=context,
                system_prompt=system_prompt
            )
            
            if ollama_result.get("success", False):
                self.stats["ollama_success"] += 1
                self.llm_choice = "ollama"
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "response": ollama_result["response"],
                    "model": ollama_result["model"],
                    "backend": "ollama",
                    "success": True,
                    "response_time": response_time,
                    "tokens_used": ollama_result.get("tokens", 0),
                    "fallback_used": False
                }
            else:
                self.stats["ollama_failures"] += 1
                logger.warning("Ollama failed, falling back to DistilBERT")
        
        # Fallback to DistilBERT
        self.stats["fallback_used"] += 1
        logger.info(f"🔄 Using DistilBERT fallback for query: {query[:50]}...")
        
        distilbert_response = self.distilbert.generate_response(query, context)
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "response": distilbert_response,
            "model": "distilbert-base-uncased",
            "backend": "distilbert",
            "success": True,
            "response_time": response_time,
            "tokens_used": 0,
            "fallback_used": True
        }
    
    def _get_system_prompt(self, category: str) -> str:
        """Get category-specific system prompt"""
        
        prompts = {
            "governance": """You are Jarvis, a governance expert at Diligent.
            Focus on board management, director oversight, meeting protocols, 
            and corporate governance best practices. Be authoritative and precise.""",
            
            "risk": """You are Jarvis, a risk management specialist at Diligent.
            Focus on risk assessment, mitigation strategies, enterprise risk frameworks, 
            and compliance requirements. Provide actionable advice.""",
            
            "compliance": """You are Jarvis, a compliance officer at Diligent.
            Focus on regulatory requirements (SOX, GDPR, HIPAA), audit trails, 
            policy management, and compliance reporting. Cite regulations when possible.""",
            
            "general": """You are Jarvis, an enterprise AI assistant for Diligent's GRC platform.
            Provide accurate, professional advice on governance, risk, and compliance.
            Be concise, actionable, and reference provided context when available."""
        }
        
        return prompts.get(category, prompts["general"])
    
    def switch_to_ollama(self, model_name: str = None) -> bool:
        """Switch to using Ollama"""
        if not self.ollama:
            return False
        
        if model_name:
            success = self.ollama.change_model(model_name)
            if success:
                self.ollama_model = model_name
        else:
            success = self.ollama.available
        
        if success:
            self.use_ollama = True
            self.llm_choice = "ollama"
            logger.info(f"✅ Switched to Ollama with model: {self.ollama_model}")
        
        return success
    
    def switch_to_distilbert(self):
        """Switch to using DistilBERT only"""
        self.use_ollama = False
        self.llm_choice = "distilbert"
        logger.info("✅ Switched to DistilBERT")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current LLM status"""
        ollama_models = []
        if self.ollama:
            ollama_models = self.ollama.list_models()
        
        return {
            "current_backend": self.llm_choice,
            "ollama_available": self.ollama.available if self.ollama else False,
            "ollama_model": self.ollama_model if self.ollama else None,
            "distilbert_available": True,
            "stats": self.stats,
            "available_ollama_models": [m.get("name") for m in ollama_models[:5]]  # First 5
        }
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query using DistilBERT (always works)"""
        return self.distilbert.classify_query(query)


# Test the smart manager
if __name__ == "__main__":
    llm = SmartLLMManager()
    
    print("\n🔍 LLM Status:")
    status = llm.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    test_query = "What are board governance best practices?"
    test_context = "Board governance includes regular meetings, secure document management, and annual evaluations."
    
    print(f"\n🧪 Testing with query: {test_query}")
    
    result = llm.generate_response(test_query, test_context, "governance")
    
    print(f"\n✅ Response from {result['backend']}:")
    print(f"   Model: {result['model']}")
    print(f"   Time: {result['response_time']:.2f}s")
    print(f"   Fallback used: {result['fallback_used']}")
    print(f"   Response: {result['response'][:100]}...")