import requests
import json
import subprocess
import time
import os

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "mistral:7b"  # 7B model fits in 8GB RAM
OLLAMA_PROCESS = None


def start_ollama():
    """Start Ollama server in background"""
    global OLLAMA_PROCESS
    try:
        if is_ollama_running():
            return True
        
        OLLAMA_PROCESS = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        return is_ollama_running()
    except Exception as e:
        print(f"Failed to start Ollama: {e}")
        return False


def is_ollama_running():
    """Check if Ollama server is running"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def pull_model():
    """Pull the Mistral model if not available"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if any(MODEL_NAME in name for name in model_names):
                return True
        
        print(f"Pulling model {MODEL_NAME}...")
        response = requests.post(
            f"{OLLAMA_HOST}/api/pull",
            json={"name": MODEL_NAME},
            stream=True,
            timeout=300
        )
        
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"Error pulling model: {e}")
    
    return False


def is_local_llm_available():
    """Check if local LLM is available and ready"""
    if not is_ollama_running():
        if not start_ollama():
            return False
    
    return pull_model()


def answer_question_local(question: str, document_context: str, document_name: str = None) -> str:
    """Answer question using local Ollama model"""
    if not document_context or document_context.strip() == "":
        return "I couldn't find any text content in the document to answer your question."
    
    context_info = f"from the document '{document_name}'" if document_name else "from the provided documents"
    
    prompt = f"""You are a helpful document assistant. Answer questions based on the document content.

Guidelines:
- Only use information from the document
- If the answer is not in the document, say so clearly
- Be concise and accurate
- Provide specific references when possible

Document: {context_info}

---
{document_context[:8000]}
---

Question: {question}

Answer:"""
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "num_predict": 1024
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Failed to generate response.").strip()
        else:
            return f"Error: Received status code {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "The local AI model took too long to respond. Please try again."
    except Exception as e:
        return f"Error generating response: {str(e)}"


def summarize_document_local(document_text: str, document_name: str = None) -> str:
    """Summarize document using local Ollama model"""
    if not document_text or document_text.strip() == "":
        return "The document appears to be empty or text extraction failed."
    
    prompt = f"""Provide a clear, concise summary of this document.

Document: {document_name if document_name else "Untitled"}

Content:
---
{document_text[:8000]}
---

Summary:"""
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "num_predict": 512
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Failed to generate summary.").strip()
        else:
            return f"Error: Received status code {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "The local AI model took too long to respond. Please try again."
    except Exception as e:
        return f"Error generating summary: {str(e)}"
