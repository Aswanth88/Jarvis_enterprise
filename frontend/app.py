# frontend/app.py
import streamlit as st
import requests
import json
from datetime import datetime
import time
import threading
from queue import Queue
import sys
import os

# Set page configuration
st.set_page_config(
    page_title="Diligent Jarvis - Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Aswanth88/Jarvis_enterprise',
        'Report a bug': "https://github.com/Aswanth88/Jarvis_enterprise/issues",
        'About': "# 🤖 Jarvis Enterprise AI Assistant\nBuilt for Diligent Internship Assessment"
    }
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        animation: fadeIn 0.5s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left: 6px solid #4F46E5;
    }
    
    .assistant-message {
        background: white;
        border: 1px solid #E5E7EB;
        border-left: 6px solid #10B981;
    }
    
    /* Status chips */
    .status-chip {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .status-ollama {
        background-color: #DBEAFE;
        color: #1E40AF;
    }
    
    .status-distilbert {
        background-color: #D1FAE5;
        color: #065F46;
    }
    
    .status-error {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    
    /* Source chips */
    .source-chip {
        display: inline-block;
        background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%);
        padding: 0.35rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #D8B4FE;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F3F4F6;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #9CA3AF;
        border-radius: 4px;
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 1rem !important;
        border: 2px solid #E5E7EB !important;
        font-size: 1rem !important;
        padding: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 1rem !important;
        font-weight: 600 !important;
        padding: 0.75rem 2rem !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "## 👋 Welcome to Jarvis Enterprise AI Assistant!\n\nI'm here to help you with **Governance, Risk, and Compliance (GRC)** questions. \n\n💡 **Try asking:**\n- What are board governance best practices?\n- Explain SOX compliance requirements\n- How to conduct risk assessment?\n- Tell me about Diligent's GRC platform\n\nI can access a knowledge base of enterprise information and provide context-aware responses.",
            "timestamp": datetime.now().isoformat(),
            "sources": ["Welcome Guide"],
            "category": "general",
            "backend": "distilbert",
            "model": "distilbert-base-uncased",
            "response_time": 0,
            "fallback_used": False
        }
    ]

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = []

if "llm_status" not in st.session_state:
    st.session_state.llm_status = {
        "current_backend": "unknown",
        "ollama_available": False,
        "available_models": []
    }

if "query_stats" not in st.session_state:
    st.session_state.query_stats = {
        "total": 0,
        "by_backend": {"ollama": 0, "distilbert": 0},
        "by_category": {},
        "avg_response_time": 0
    }

if "user_name" not in st.session_state:
    st.session_state.user_name = "Enterprise User"

# Helper functions
def check_backend_health():
    """Check if backend is available"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"Status code: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Cannot connect to backend"}
    except Exception as e:
        return False, {"error": str(e)}

def get_llm_status():
    """Get LLM backend status"""
    try:
        response = requests.get(f"{API_BASE}/llm/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            st.session_state.llm_status = {
                "current_backend": data["status"]["current_backend"],
                "ollama_available": data["status"]["ollama_available"],
                "available_models": data["status"].get("available_ollama_models", []),
                "stats": data["status"].get("stats", {})
            }
            return True
    except:
        pass
    return False

def switch_backend(backend, model_name=None):
    """Switch between Ollama and DistilBERT"""
    try:
        payload = {"backend": backend}
        if model_name:
            payload["model_name"] = model_name
            
        response = requests.post(f"{API_BASE}/llm/switch", 
                               json=payload, 
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("success", False), data.get("message", "")
    except:
        pass
    return False, "Failed to switch backend"

def add_knowledge_to_base(text, category, tags):
    """Add new knowledge to the system"""
    try:
        response = requests.post(f"{API_BASE}/knowledge", json={
            "text": text,
            "category": category,
            "tags": tags,
            "source": "web_interface"
        }, timeout=10)
        
        if response.status_code == 200:
            return True, "Knowledge added successfully!"
        else:
            return False, f"Error: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def search_knowledge(query, limit=5):
    """Search the knowledge base"""
    try:
        response = requests.get(f"{API_BASE}/search/{query}?limit={limit}", timeout=5)
        if response.status_code == 200:
            return True, response.json()["results"]
        else:
            return False, []
    except:
        return False, []

def submit_feedback(query, response, rating, comment=""):
    """Submit feedback for responses"""
    try:
        requests.post(f"{API_BASE}/feedback", json={
            "query": query,
            "response": response,
            "rating": rating,
            "feedback": comment
        }, timeout=2)
    except:
        pass

# Initialize status
backend_healthy, health_data = check_backend_health()
get_llm_status()

# Sidebar
with st.sidebar:
    # Header with logo
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3079/3079165.png", width=50)
    with col2:
        st.markdown("### Jarvis Control")
    
    st.markdown("---")
    
    # Backend Health Status
    st.subheader("🔧 System Status")
    
    if backend_healthy:
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.success("✅ Backend")
        with status_col2:
            if health_data["components"]["llm"].startswith("ollama"):
                st.success("✅ Ollama")
            else:
                st.info("⚡ DistilBERT")
        
        # Quick stats
        if st.session_state.llm_status.get("stats"):
            stats = st.session_state.llm_status["stats"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", stats.get("total_queries", 0))
            with col2:
                st.metric("Fallbacks", stats.get("fallback_used", 0))
    else:
        st.error("❌ Backend Offline")
        st.info("Start backend with: `cd backend && python app.py`")
    
    st.markdown("---")
    
    # AI Backend Control
    st.subheader("🤖 AI Configuration")
    
    # Backend selector
    backend_options = ["Auto-select", "Ollama", "DistilBERT"]
    selected_backend = st.selectbox(
        "Primary Backend",
        backend_options,
        index=0
    )
    
    # If Ollama is selected and available, show model selector
    if (selected_backend == "Ollama" or selected_backend == "Auto-select") and st.session_state.llm_status["ollama_available"]:
        models = st.session_state.llm_status["available_models"]
        if models:
            selected_model = st.selectbox("Ollama Model", models)
            if st.button("Apply Configuration"):
                with st.spinner("Switching backend..."):
                    success, message = switch_backend("ollama", selected_model)
                    if success:
                        st.success(f"Switched to Ollama ({selected_model})")
                        get_llm_status()
                    else:
                        st.warning(message)
    
    # Manual switch buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Use Ollama", 
                    disabled=not st.session_state.llm_status["ollama_available"],
                    help="Use Ollama for higher quality responses"):
            success, message = switch_backend("ollama")
            if success:
                st.success("Switched to Ollama")
                get_llm_status()
                st.rerun()
            else:
                st.warning(message)
    
    with col2:
        if st.button("⚡ Use DistilBERT", 
                    help="Use DistilBERT for faster responses"):
            success, message = switch_backend("distilbert")
            if success:
                st.info("Switched to DistilBERT")
                get_llm_status()
                st.rerun()
    
    # Current status
    st.markdown("**Current Status:**")
    current_backend = st.session_state.llm_status["current_backend"]
    if current_backend == "ollama":
        st.markdown('<span class="status-chip status-ollama">Ollama Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-chip status-distilbert">DistilBERT Active</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Knowledge Base Management
    st.subheader("📚 Knowledge Base")
    
    # Quick search
    search_query = st.text_input("🔍 Search knowledge", key="search_box")
    if search_query:
        success, results = search_knowledge(search_query, 3)
        if success and results:
            with st.expander(f"Found {len(results)} results", expanded=True):
                for i, result in enumerate(results):
                    st.markdown(f"**{i+1}. {result['category']}** (Score: {result['score']:.3f})")
                    st.caption(result['text'][:150] + "...")
        elif search_query:
            st.info("No results found")
    
    # Add new knowledge
    with st.expander("➕ Add New Knowledge", expanded=False):
        with st.form("add_knowledge_form"):
            new_text = st.text_area("Knowledge text:", height=100,
                                  placeholder="Enter enterprise knowledge...")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", 
                                      ["governance", "risk", "compliance", "technology", "company", "general"])
            with col2:
                tags_input = st.text_input("Tags (comma separated)")
            
            submitted = st.form_submit_button("💾 Add to Knowledge Base")
            
            if submitted and new_text:
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                with st.spinner("Adding knowledge..."):
                    success, message = add_knowledge_to_base(new_text, category, tags)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # Quick queries
    st.markdown("---")
    st.subheader("💡 Quick Queries")
    
    quick_queries = [
        "What is enterprise governance?",
        "Explain SOX compliance",
        "How to manage board meetings?",
        "What is risk assessment?",
        "Tell me about Diligent"
    ]
    
    for query in quick_queries:
        if st.button(f"🗨️ {query}", key=f"quick_{hash(query)}"):
            st.session_state.user_input = query
            st.rerun()
    
    # User info
    st.markdown("---")
    with st.expander("👤 User Settings", expanded=False):
        st.session_state.user_name = st.text_input("Your Name", 
                                                  value=st.session_state.user_name)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("**Powered by:**")
    st.caption("• Ollama/LLaMA • DistilBERT • Pinecone • Streamlit")
    st.caption(f"**Version:** 2.0 • **User:** {st.session_state.user_name}")
    st.caption("Built for Diligent Internship Assessment")

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    # Header with stats
    st.markdown('<div class="main-header">🤖 Jarvis Enterprise AI</div>', unsafe_allow_html=True)
    
    # Stats bar
    if st.session_state.query_stats["total"] > 0:
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Total Queries", st.session_state.query_stats["total"])
        with col_stats2:
            ollama_pct = (st.session_state.query_stats["by_backend"]["ollama"] / 
                         st.session_state.query_stats["total"] * 100) if st.session_state.query_stats["total"] > 0 else 0
            st.metric("Ollama Usage", f"{ollama_pct:.1f}%")
        with col_stats3:
            st.metric("Avg Response", f"{st.session_state.query_stats['avg_response_time']:.2f}s")
    
    st.markdown('<div class="sub-header">Your AI Assistant for Governance, Risk & Compliance</div>', unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    
    # Display messages
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; margin-right: 0.75rem;">
                            <span style="color: #667eea; font-weight: bold;">{st.session_state.user_name[0].upper()}</span>
                        </div>
                        <div>
                            <strong>{st.session_state.user_name}</strong>
                            <div style="font-size: 0.8rem; opacity: 0.9;">
                                {datetime.fromisoformat(message['timestamp']).strftime('%I:%M %p')}
                            </div>
                        </div>
                    </div>
                    <div style="margin-left: 3rem;">
                        {message['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message
                backend_badge = ""
                if message.get("backend") == "ollama":
                    backend_badge = '<span class="status-chip status-ollama">Ollama</span>'
                elif message.get("backend") == "distilbert":
                    backend_badge = '<span class="status-chip status-distilbert">DistilBERT</span>'
                
                fallback_indicator = ""
                if message.get("fallback_used"):
                    fallback_indicator = '⚠️ <span style="font-size: 0.8rem; color: #F59E0B;">(Fallback used)</span>'
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #10B981 0%, #059669 100%); display: flex; align-items: center; justify-content: center; margin-right: 0.75rem;">
                            <span style="color: white; font-weight: bold;">J</span>
                        </div>
                        <div style="flex: 1;">
                            <strong>Jarvis Assistant</strong>
                            <div style="font-size: 0.8rem; color: #6B7280;">
                                {datetime.fromisoformat(message['timestamp']).strftime('%I:%M %p')} • 
                                {backend_badge} {fallback_indicator}
                            </div>
                        </div>
                        <div style="font-size: 0.8rem; color: #6B7280;">
                            {message.get('response_time', 0):.2f}s
                        </div>
                    </div>
                    
                    <div style="margin-left: 3rem; margin-bottom: 1rem;">
                        {message['content']}
                    </div>
                """, unsafe_allow_html=True)
                
                # Sources if available
                if message.get("sources"):
                    st.markdown("""
                    <div style="margin-left: 3rem; margin-top: 0.5rem;">
                        <div style="font-size: 0.85rem; color: #6B7280; margin-bottom: 0.25rem;">
                            <strong>📚 Sources:</strong>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    for source in message["sources"]:
                        st.markdown(f'<span class="source-chip">{source}</span>', unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Feedback buttons (only for assistant messages that aren't the welcome)
                if message != st.session_state.messages[0]:
                    col_f1, col_f2, col_f3 = st.columns([1, 1, 8])
                    with col_f1:
                        if st.button("👍", key=f"like_{hash(str(message))}", 
                                   help="This response was helpful"):
                            submit_feedback(
                                st.session_state.messages[-2]["content"] if len(st.session_state.messages) > 1 else "",
                                message["content"],
                                5
                            )
                            st.toast("Thanks for your feedback! 👍")
                    with col_f2:
                        if st.button("👎", key=f"dislike_{hash(str(message))}", 
                                   help="This response needs improvement"):
                            submit_feedback(
                                st.session_state.messages[-2]["content"] if len(st.session_state.messages) > 1 else "",
                                message["content"],
                                1
                            )
                            st.toast("Thanks for your feedback! We'll improve. 👎")
                
                st.markdown("</div>", unsafe_allow_html=True)

with col2:
    # Right sidebar - Insights & Analytics
    st.subheader("📊 Live Insights")
    
    # Query categories chart
    if st.session_state.query_stats["by_category"]:
        st.markdown("**Query Categories:**")
        for category, count in st.session_state.query_stats["by_category"].items():
            st.progress(min(count / 10, 1.0), text=f"{category}: {count}")
    
    # Backend usage
    st.markdown("**AI Backend Usage:**")
    if st.session_state.query_stats["total"] > 0:
        ollama_count = st.session_state.query_stats["by_backend"]["ollama"]
        distilbert_count = st.session_state.query_stats["by_backend"]["distilbert"]
        
        col_ollama, col_distilbert = st.columns(2)
        with col_ollama:
            st.metric("Ollama", ollama_count)
        with col_distilbert:
            st.metric("DistilBERT", distilbert_count)
    
    # Recent knowledge additions
    st.markdown("---")
    st.markdown("**🧠 Recent Knowledge:**")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=3)
        if response.status_code == 200:
            stats = response.json()
            if "knowledge_base" in stats:
                kb_stats = stats["knowledge_base"]
                st.metric("Total Documents", kb_stats.get("total_documents", 0))
                
                # Categories breakdown
                if "documents_per_category" in kb_stats:
                    with st.expander("By Category"):
                        for category, count in kb_stats["documents_per_category"].items():
                            st.caption(f"{category}: {count}")
    except:
        st.info("Knowledge stats unavailable")
    
    # Tips panel
    st.markdown("---")
    st.markdown("**💡 Tips for Better Results:**")
    
    tips = [
        "Be specific in your questions",
        "Mention if you want technical or business answers",
        "Ask follow-up questions for clarification",
        "Use the 'Add Knowledge' feature for domain-specific info"
    ]
    
    for i, tip in enumerate(tips):
        st.caption(f"{i+1}. {tip}")
    
    # System info
    st.markdown("---")
    st.markdown("**⚙️ System Info:**")
    
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.caption("Backend: Running" if backend_healthy else "Backend: Offline")
    with info_col2:
        st.caption("Memory: Stable")

# Chat input at bottom
st.markdown("---")

# Two-column layout for input
input_col1, input_col2 = st.columns([5, 1])

with input_col1:
    user_input = st.text_input(
        "query_input",
        placeholder=f"Ask {st.session_state.user_name}, what's on your mind about GRC?",
        key="user_input",
        label_visibility="collapsed"
    )

with input_col2:
    send_button = st.button("🚀 Send", use_container_width=True)

# Handle send
if send_button and user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Clear input
    st.session_state.user_input = ""
    
    # Create a placeholder for streaming response
    response_placeholder = st.empty()
    
    # Show thinking indicator
    with response_placeholder.container():
        col_thinking1, col_thinking2 = st.columns([1, 20])
        with col_thinking1:
            st.spinner("thinking")
        with col_thinking2:
            st.info("Jarvis is thinking...")
    
    try:
        # Call API
        start_time = time.time()
        response = requests.post(f"{API_BASE}/query", json={
            "message": user_input,
            "user_id": st.session_state.user_name
        }, timeout=30)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Update query statistics
            st.session_state.query_stats["total"] += 1
            backend = data.get("backend", "distilbert")
            st.session_state.query_stats["by_backend"][backend] += 1
            
            category = data.get("category", "general")
            if category not in st.session_state.query_stats["by_category"]:
                st.session_state.query_stats["by_category"][category] = 0
            st.session_state.query_stats["by_category"][category] += 1
            
            # Update average response time
            current_avg = st.session_state.query_stats["avg_response_time"]
            total_queries = st.session_state.query_stats["total"]
            new_avg = ((current_avg * (total_queries - 1)) + data.get("response_time", 0)) / total_queries
            st.session_state.query_stats["avg_response_time"] = new_avg
            
            # Add assistant response
            assistant_message = {
                "role": "assistant",
                "content": data["response"],
                "timestamp": data["timestamp"],
                "sources": data["sources"],
                "category": category,
                "backend": backend,
                "model": data["model"],
                "response_time": data.get("response_time", 0),
                "fallback_used": data.get("fallback_used", False)
            }
            
            st.session_state.messages.append(assistant_message)
            
            # Clear placeholder and rerun to show new message
            response_placeholder.empty()
            st.rerun()
            
        else:
            response_placeholder.error(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        response_placeholder.error("Cannot connect to Jarvis backend. Please ensure it's running on http://localhost:8000")
    except requests.exceptions.Timeout:
        response_placeholder.warning("Request timed out. The AI might be processing a complex query.")
    except Exception as e:
        response_placeholder.error(f"Unexpected error: {str(e)}")

# Footer
st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("**Built With**")
    st.caption("• FastAPI • Hugging Face • Streamlit")

with footer_col2:
    st.caption("**For Diligent**")
    st.caption("• GRC Focus • Enterprise Ready • Secure")

with footer_col3:
    # Refresh status button
    if st.button("🔄 Refresh Status", key="refresh_status"):
        backend_healthy, health_data = check_backend_health()
        get_llm_status()
        st.rerun()

# Auto-refresh status every 30 seconds
if "last_status_check" not in st.session_state:
    st.session_state.last_status_check = time.time()

current_time = time.time()
if current_time - st.session_state.last_status_check > 30:  # 30 seconds
    backend_healthy, health_data = check_backend_health()
    get_llm_status()
    st.session_state.last_status_check = current_time

# Display connection warning if backend is down
if not backend_healthy:
    st.warning("""
    ⚠️ **Backend Connection Issue**
    
    The Jarvis backend appears to be offline. Please ensure:
    1. Backend is running: `cd backend && python app.py`
    2. Port 8000 is not blocked
    3. Dependencies are installed: `pip install -r requirements.txt`
    
    You can still type messages, but they won't be processed until the backend is running.
    """)

# Display welcome message for new users
if len(st.session_state.messages) == 1:
    st.balloons()
    st.success("✨ Welcome to Jarvis Enterprise AI Assistant! Start by asking a question about governance, risk, or compliance.")

# Keyboard shortcut hint
st.caption("💡 **Tip**: Press Enter to send, Shift+Enter for new line")