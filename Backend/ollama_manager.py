# backend/ollama_manager.py (updated)
import requests
import json
import time
from typing import Optional, Dict, Any
from config import OllamaConfig

class OllamaManager:
    """Improved Ollama manager with better error handling"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.base_url = OllamaConfig.BASE_URL
        
        # Auto-select best model if not specified
        if model_name:
            self.model = model_name
        else:
            self.model = OllamaConfig.get_best_available_model() or "llama2:7b"
        
        self.is_available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if Ollama is available with retries"""
        for attempt in range(3):
            try:
                response = requests.get(
                    f"{self.base_url}/api/tags",
                    timeout=OllamaConfig.TIMEOUT_CONNECT
                )
                
                if response.status_code == 200:
                    print(f"✅ Ollama available with model: {self.model}")
                    return True
                    
                time.sleep(1)  # Wait before retry
                
            except Exception as e:
                print(f"⚠️ Ollama check attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        
        print("❌ Ollama not available after retries")
        return False
    
    def generate(self, prompt: str, context: str = "", system_prompt: str = None) -> Dict[str, Any]:
        """Generate response with improved error handling"""
        if not self.is_available:
            return {"error": "Ollama not available"}
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_prompt)
        
        # Get generation parameters
        params = OllamaConfig.get_generation_params(self.model)
        params["prompt"] = full_prompt
        
        try:
            start_time = time.time()
            
            # First try normal generation
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=params,
                timeout=OllamaConfig.TIMEOUT_READ
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", "").strip(),
                    "model": self.model,
                    "response_time": elapsed,
                    "tokens_used": result.get("total_duration", 0),
                    "success": True
                }
            else:
                print(f"❌ Ollama generation failed: {response.status_code}")
                
                # Try streaming as fallback
                return self._try_streaming_generation(full_prompt)
                
        except requests.exceptions.Timeout:
            print(f"⏰ Ollama generation timeout with {self.model}")
            
            # Switch to a smaller model if available
            return self._try_smaller_model(full_prompt)
            
        except Exception as e:
            print(f"❌ Ollama generation error: {e}")
            return {"error": str(e), "success": False}
    
    def _try_streaming_generation(self, prompt: str) -> Dict[str, Any]:
        """Try streaming generation (more responsive)"""
        try:
            params = OllamaConfig.get_generation_params(self.model)
            params["prompt"] = prompt
            params["stream"] = True
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=params,
                stream=True,
                timeout=OllamaConfig.TIMEOUT_READ
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            full_response += data.get("response", "")
                        except:
                            continue
                
                return {
                    "response": full_response.strip(),
                    "model": f"{self.model} (stream)",
                    "response_time": 0,
                    "success": True
                }
                
        except Exception as e:
            print(f"❌ Streaming also failed: {e}")
            
        return {"error": "Generation failed", "success": False}
    
    def _try_smaller_model(self, prompt: str) -> Dict[str, Any]:
        """Try a smaller model"""
        smaller_models = ["tinyllama", "phi", "llama2:7b"]
        
        for model in smaller_models:
            if model == self.model:
                continue
                
            print(f"🔄 Trying smaller model: {model}")
            
            try:
                params = OllamaConfig.get_generation_params(model)
                params["prompt"] = prompt
                params["options"]["num_predict"] = 128  # Very short
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=params,
                    timeout=30  # Short timeout for small model
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": result.get("response", "").strip(),
                        "model": f"{model} (fallback)",
                        "response_time": 0,
                        "tokens_used": 0,
                        "fallback_used": True,
                        "success": True
                    }
                    
            except:
                continue
        
        return {"error": "All models failed", "success": False}
    
    def _build_prompt(self, prompt: str, context: str, system_prompt: str = None) -> str:
        """Build a well-formatted prompt"""
        if not system_prompt:
            system_prompt = "You are Jarvis, an AI assistant for enterprise governance, risk, and compliance (GRC). Provide helpful, accurate responses based on the context."
        
        if context:
            return f"""{system_prompt}

Context information:
{context}

Based on the context above, answer the following question:

Question: {prompt}

Answer:"""
        else:
            return f"""{system_prompt}

Question: {prompt}

Answer:"""