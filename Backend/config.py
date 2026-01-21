# backend/config.py
import os
from typing import Optional

class OllamaConfig:
    """Ollama configuration with better defaults"""
    
    # Base URL for Ollama
    BASE_URL = "http://localhost:11434"
    
    # Model preferences (in order of preference)
    PREFERRED_MODELS = [
        "llama2:7b",          # Smaller, faster
        "mistral:instruct",   # Instruct-tuned version
        "mistral",            # Base mistral
        "phi",                # Very small, fast
        "tinyllama"           # Fastest
    ]
    
    # Timeout settings (in seconds)
    TIMEOUT_CONNECT = 10
    TIMEOUT_READ = 180        # 3 minutes for generation
    TIMEOUT_WRITE = 60
    
    # Generation settings
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 512
    
    @classmethod
    def get_best_available_model(cls) -> Optional[str]:
        """Get the best available model"""
        import requests
        
        try:
            response = requests.get(
                f"{cls.BASE_URL}/api/tags",
                timeout=cls.TIMEOUT_CONNECT
            )
            
            if response.status_code == 200:
                available_models = [m["name"] for m in response.json().get("models", [])]
                
                # Return first preferred model that's available
                for model in cls.PREFERRED_MODELS:
                    if model in available_models:
                        print(f"✅ Selected Ollama model: {model}")
                        return model
                
                # If no preferred models, use first available
                if available_models:
                    print(f"⚠️ Using available model: {available_models[0]}")
                    return available_models[0]
                    
        except Exception as e:
            print(f"❌ Cannot check available models: {e}")
            
        return None
    
    @classmethod
    def get_generation_params(cls, model: str) -> dict:
        """Get optimal parameters for a model"""
        params = {
            "model": model,
            "stream": False,
            "options": {
                "temperature": cls.DEFAULT_TEMPERATURE,
                "num_predict": cls.DEFAULT_MAX_TOKENS,
            }
        }
        
        # Model-specific optimizations
        if "llama2" in model:
            params["options"]["num_ctx"] = 4096
        elif "mistral" in model:
            params["options"]["num_ctx"] = 8192
        elif "tiny" in model:
            params["options"]["num_predict"] = 256  # Shorter for tiny models
            
        return params