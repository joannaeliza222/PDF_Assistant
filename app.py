import streamlit as st
from datetime import datetime
from models import init_db, SessionLocal, Document, ChatHistory
from pdf_processor import extract_text_from_pdf, get_pdf_info
from gemini_ai import answer_question, summarize_document, is_api_configured

st.set_page_config(
    page_title="PDF Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #F8FAFC;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    h1, h2, h3 {
        color: #1E293B;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .upload-section h2 {
        color: white !important;
        margin-bottom: 1rem;
    }
    
    .upload-section p {
        color: rgba(255, 255, 255, 0.9);
    }
    
    .document-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .document-card:hover {
        border-color: #6366F1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }
    
    .document-card.selected {
        border-color: #6366F1;
        background: #F5F3FF;
    }
    
    .document-title {
        font-weight: 600;
        color: #1E293B;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    
    .document-meta {
        font-size: 0.75rem;
        color: #64748B;
    }
    
    .chat-container {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1.5rem;
        height: 600px;
        display: flex;
        flex-direction: column;
        border: 1px solid #E2E8F0;
    }
    
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 1rem;
    }
    
    .message-user {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px 12px 4px 12px;
        margin-bottom: 0.75rem;
        max-width: 80%;
        margin-left: auto;
    }
    
    .message-assistant {
        background: #F1F5F9;
        color: #1E293B;
        padding: 0.75rem 1rem;
        border-radius: 12px 12px 12px 4px;
        margin-bottom: 0.75rem;
        max-width: 80%;
    }
    
    .stats-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    .stats-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: #6366F1;
    }
    
    .stats-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .success-badge {
        background: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .scanned-badge {
        background: #F59E0B;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6366F1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .sidebar .sidebar-content {
        background: #FFFFFF;
    }
    
    div[data-testid="stFileUploader"] {
        background: white;
        border-radius: 12px;
        padding: 1rem;
    }
    
    .header-gradient {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
</style>
""", unsafe_allow_html=True)

init_db()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_document" not in st.session_state:
    st.session_state.selected_document = None
if "all_documents_mode" not in st.session_state:
    st.session_state.all_documents_mode = False


def get_all_documents():
    db = SessionLocal()
    try:
        documents = db.query(Document).order_by(Document.upload_date.desc()).all()
        return documents
    finally:
        db.close()


def get_document_by_id(doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        return document
    finally:
        db.close()


def save_document(filename, file_data, extracted_text, page_count, file_size, is_scanned):
    db = SessionLocal()
    try:
        document = Document(
            filename=filename,
            file_data=file_data,
            extracted_text=extracted_text,
            page_count=page_count,
            file_size=file_size,
            is_scanned=1 if is_scanned else 0
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id
    finally:
        db.close()


def delete_document(doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            db.query(ChatHistory).filter(ChatHistory.document_id == doc_id).delete()
            db.delete(document)
            db.commit()
            return True
        return False
    finally:
        db.close()


def save_chat_history(document_id, question, answer):
    db = SessionLocal()
    try:
        chat = ChatHistory(
            document_id=document_id,
            question=question,
            answer=answer
        )
        db.add(chat)
        db.commit()
    finally:
        db.close()


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


st.markdown('<h1 style="text-align: center;">📄 <span class="header-gradient">PDF Document Assistant</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B; margin-bottom: 2rem;">Upload PDFs and ask questions about your documents using AI</p>', unsafe_allow_html=True)

if not is_api_configured():
    st.warning("⚠️ AI features are disabled. Please configure your GEMINI_API_KEY in the Secrets tab to enable AI-powered Q&A.")

left_col, right_col = st.columns([1, 1.5], gap="large")

with left_col:
    st.markdown("### 📤 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Drag and drop a PDF file here",
        type=["pdf"],
        help="Supports both regular and scanned PDFs"
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_size = len(file_bytes)
        
        existing_docs = get_all_documents()
        existing_names = [doc.filename for doc in existing_docs]
        
        if uploaded_file.name not in existing_names:
            with st.spinner("Processing PDF... This may take a moment for scanned documents."):
                try:
                    extracted_text, page_count, is_scanned = extract_text_from_pdf(file_bytes)
                    
                    doc_id = save_document(
                        filename=uploaded_file.name,
                        file_data=file_bytes,
                        extracted_text=extracted_text,
                        page_count=page_count,
                        file_size=file_size,
                        is_scanned=is_scanned
                    )
                    
                    st.session_state.selected_document = doc_id
                    
                    if is_scanned:
                        st.success(f"✅ Scanned PDF uploaded successfully! Extracted text using OCR.")
                    else:
                        st.success(f"✅ PDF uploaded and processed successfully!")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to process PDF: {str(e)}")
        else:
            st.info("This document has already been uploaded.")
    
    st.markdown("---")
    st.markdown("### 📚 Document Library")
    
    documents = get_all_documents()
    
    if documents:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="stats-card"><div class="stats-number">{len(documents)}</div><div class="stats-label">Documents</div></div>', unsafe_allow_html=True)
        with col2:
            total_pages = sum(doc.page_count for doc in documents)
            st.markdown(f'<div class="stats-card"><div class="stats-number">{total_pages}</div><div class="stats-label">Total Pages</div></div>', unsafe_allow_html=True)
        with col3:
            scanned_count = sum(1 for doc in documents if doc.is_scanned)
            st.markdown(f'<div class="stats-card"><div class="stats-number">{scanned_count}</div><div class="stats-label">Scanned</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        search_all = st.checkbox("🔍 Search across all documents", value=st.session_state.all_documents_mode)
        st.session_state.all_documents_mode = search_all
        
        if not search_all:
            st.markdown("**Select a document to chat with:**")
        
        for doc in documents:
            is_selected = st.session_state.selected_document == doc.id and not search_all
            
            col_doc, col_delete = st.columns([5, 1])
            
            with col_doc:
                badge = '<span class="scanned-badge">OCR</span>' if doc.is_scanned else '<span class="success-badge">Text</span>'
                
                card_class = "document-card selected" if is_selected else "document-card"
                
                st.markdown(f'''
                <div class="{card_class}">
                    <div class="document-title">📄 {doc.filename} {badge}</div>
                    <div class="document-meta">{doc.page_count} pages • {format_file_size(doc.file_size)} • {doc.upload_date.strftime("%b %d, %Y")}</div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"Select", key=f"select_{doc.id}", use_container_width=True):
                    st.session_state.selected_document = doc.id
                    st.session_state.all_documents_mode = False
                    st.session_state.messages = []
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{doc.id}", help="Delete document"):
                    if delete_document(doc.id):
                        if st.session_state.selected_document == doc.id:
                            st.session_state.selected_document = None
                            st.session_state.messages = []
                        st.rerun()
    else:
        st.info("No documents uploaded yet. Upload your first PDF to get started!")

with right_col:
    st.markdown("### 💬 Chat with Documents")
    
    if st.session_state.all_documents_mode:
        st.markdown('<div style="background: #F5F3FF; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;"><span style="color: #6366F1; font-weight: 500;">🔍 Searching across all documents</span></div>', unsafe_allow_html=True)
        context_docs = get_all_documents()
        combined_context = ""
        for doc in context_docs:
            if doc.extracted_text:
                combined_context += f"\n\n--- Document: {doc.filename} ---\n{doc.extracted_text}"
        document_context = combined_context
        current_doc_name = "All Documents"
        current_doc_id = None
    elif st.session_state.selected_document:
        current_doc = get_document_by_id(st.session_state.selected_document)
        if current_doc:
            st.markdown(f'<div style="background: #F5F3FF; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;"><span style="color: #6366F1; font-weight: 500;">📄 Chatting with: {current_doc.filename}</span></div>', unsafe_allow_html=True)
            document_context = current_doc.extracted_text
            current_doc_name = current_doc.filename
            current_doc_id = current_doc.id
        else:
            document_context = None
            current_doc_name = None
            current_doc_id = None
    else:
        document_context = None
        current_doc_name = None
        current_doc_id = None
    
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.messages:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'<div class="message-user">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="message-assistant">{message["content"]}</div>', unsafe_allow_html=True)
        elif document_context:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #64748B;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💭</div>
                <p>Ask any question about your document!</p>
                <p style="font-size: 0.85rem;">Try: "What is this document about?" or "Summarize the key points"</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #64748B;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                <p>Upload a document or select one from your library to start chatting!</p>
            </div>
            """, unsafe_allow_html=True)
    
    if document_context:
        col_input, col_btn = st.columns([5, 1])
        
        with col_input:
            user_question = st.text_input(
                "Ask a question",
                placeholder="Type your question here...",
                key="user_input",
                label_visibility="collapsed"
            )
        
        with col_btn:
            send_button = st.button("Send", use_container_width=True)
        
        col_summary, col_clear = st.columns(2)
        
        with col_summary:
            if st.button("📝 Summarize Document", use_container_width=True):
                with st.spinner("Generating summary..."):
                    summary = summarize_document(document_context, current_doc_name)
                    st.session_state.messages.append({"role": "user", "content": "Summarize this document"})
                    st.session_state.messages.append({"role": "assistant", "content": summary})
                    if current_doc_id:
                        save_chat_history(current_doc_id, "Summarize this document", summary)
                    st.rerun()
        
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        if send_button and user_question:
            st.session_state.messages.append({"role": "user", "content": user_question})
            
            with st.spinner("Thinking..."):
                answer = answer_question(user_question, document_context, current_doc_name)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                if current_doc_id:
                    save_chat_history(current_doc_id, user_question, answer)
            
            st.rerun()

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #94A3B8; font-size: 0.85rem;">PDF Document Assistant • Powered by AI</p>',
    unsafe_allow_html=True
)
