import os
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
client = None
USE_LOCAL_LLM = os.environ.get("USE_LOCAL_LLM", "false").lower() == "true"

if API_KEY:
    client = genai.Client(api_key=API_KEY)


def is_api_configured():
    """Check if either Gemini or local LLM is configured"""
    if USE_LOCAL_LLM:
        try:
            from local_llm import is_local_llm_available
            return is_local_llm_available()
        except:
            pass
    return client is not None


def answer_question(question: str, document_context: str, document_name: str = None) -> str:
    if not is_api_configured():
        return "AI features are not available. Please configure either GEMINI_API_KEY or enable local LLM to use AI-powered Q&A."
    
    if not document_context or document_context.strip() == "":
        return "I couldn't find any text content in the document to answer your question. The document might be empty or the text extraction failed."
    
    # Use local LLM if enabled
    if USE_LOCAL_LLM:
        try:
            from local_llm import answer_question_local
            return answer_question_local(question, document_context, document_name)
        except Exception as e:
            return f"Error with local LLM: {str(e)}"
    
    # Fallback to Gemini
    if not client:
        return "Gemini API is not configured."
    
    context_info = f"from the document '{document_name}'" if document_name else "from the provided documents"
    
    system_prompt = f"""You are an intelligent document assistant. Your role is to answer questions based on the content {context_info}.

Guidelines:
- Only answer questions based on the provided document content
- If the answer is not found in the document, clearly state that
- Provide specific references or quotes from the document when possible
- Be concise but thorough in your responses
- If asked about something outside the document scope, politely redirect to document-related questions"""

    prompt = f"""Document Content:
---
{document_context}
---

User Question: {question}

Please provide a helpful and accurate answer based on the document content above."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(role="user", parts=[types.Part(text=prompt)])
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )
        
        return response.text if response.text else "I couldn't generate a response. Please try again."
    
    except Exception as e:
        return f"An error occurred while processing your question: {str(e)}"


def summarize_document(document_text: str, document_name: str = None) -> str:
    if not is_api_configured():
        return "AI features are not available. Please configure either GEMINI_API_KEY or enable local LLM to use document summarization."
    
    if not document_text or document_text.strip() == "":
        return "The document appears to be empty or the text extraction failed."
    
    # Use local LLM if enabled
    if USE_LOCAL_LLM:
        try:
            from local_llm import summarize_document_local
            return summarize_document_local(document_text, document_name)
        except Exception as e:
            return f"Error with local LLM: {str(e)}"
    
    # Fallback to Gemini
    if not client:
        return "Gemini API is not configured."
    
    prompt = f"""Please provide a comprehensive summary of the following document:

Document: {document_name if document_name else "Untitled Document"}

Content:
---
{document_text[:50000]}
---

Please include:
1. Main topics and themes
2. Key points and findings
3. Important conclusions or recommendations (if any)"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "Failed to generate summary."
    
    except Exception as e:
        return f"An error occurred while summarizing: {str(e)}"
