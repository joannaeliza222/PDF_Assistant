import streamlit as st
import json
import os
from datetime import datetime
from models import init_db, SessionLocal, Document, ChatHistory, Tag, document_tags
from pdf_processor import extract_text_from_pdf, get_pdf_info
from gemini_ai import answer_question, summarize_document, is_api_configured
from pdf_viewer import get_pdf_page_as_image, get_pdf_page_count
from security import (
    sanitize_input, sanitize_filename, validate_pdf_file, 
    check_rate_limit, sanitize_for_display, validate_search_query,
    get_client_identifier, log_security_event, hash_password, verify_password,
    sanitize_extracted_text
)

st.set_page_config(
    page_title="PDF Document Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

APP_PASSWORD_HASH = os.environ.get("APP_PASSWORD_HASH", "")
REQUIRE_AUTH = os.environ.get("REQUIRE_AUTH", "true").lower() == "true"

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
    
    .tag-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 500;
        margin-right: 0.25rem;
        margin-top: 0.25rem;
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
    
    .pdf-viewer-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    .pdf-navigation {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .search-highlight {
        background-color: #FEF08A;
        padding: 0.1rem 0.2rem;
        border-radius: 2px;
    }
    
    .category-select {
        margin-top: 0.5rem;
    }
    
    .security-badge {
        background: #10B981;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.1);
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
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"
if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = 100
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "compare_docs" not in st.session_state:
    st.session_state.compare_docs = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "client_id" not in st.session_state:
    st.session_state.client_id = get_client_identifier()
else:
    st.session_state.client_id = get_client_identifier(st.session_state.client_id)
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0


def check_authentication():
    if not REQUIRE_AUTH:
        return True
    if not APP_PASSWORD_HASH:
        return True
    return st.session_state.authenticated


def show_login_page():
    st.markdown('<h1 style="text-align: center;">🔐 <span class="header-gradient">Secure Access Required</span></h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #64748B; margin-bottom: 2rem;">Please enter the password to access your documents</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🔓 Unlock", use_container_width=True)
            
            if submit:
                if st.session_state.failed_attempts >= 5:
                    st.error("Too many failed attempts. Please try again later.")
                    log_security_event("LOGIN_BLOCKED", "Too many failed attempts", st.session_state.client_id)
                    return
                
                if verify_password(password, APP_PASSWORD_HASH):
                    st.session_state.authenticated = True
                    st.session_state.failed_attempts = 0
                    log_security_event("LOGIN_SUCCESS", "User authenticated successfully", st.session_state.client_id)
                    st.rerun()
                else:
                    st.session_state.failed_attempts += 1
                    log_security_event("LOGIN_FAILED", f"Failed attempt {st.session_state.failed_attempts}", st.session_state.client_id)
                    st.error("Invalid password. Please try again.")
        
        st.markdown("---")
        st.markdown('<p style="text-align: center; color: #94A3B8; font-size: 0.8rem;">🔒 Your documents are protected with password authentication</p>', unsafe_allow_html=True)


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
    safe_filename = sanitize_filename(filename)
    safe_text = extracted_text
    
    db = SessionLocal()
    try:
        document = Document(
            filename=safe_filename,
            file_data=file_data,
            extracted_text=safe_text,
            page_count=page_count,
            file_size=file_size,
            is_scanned=1 if is_scanned else 0
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        log_security_event("DOCUMENT_UPLOADED", f"File: {safe_filename}", st.session_state.client_id)
        return document.id
    finally:
        db.close()


def delete_document(doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            filename = document.filename
            db.query(ChatHistory).filter(ChatHistory.document_id == doc_id).delete()
            db.delete(document)
            db.commit()
            log_security_event("DOCUMENT_DELETED", f"File: {filename}", st.session_state.client_id)
            return True
        return False
    finally:
        db.close()


def save_chat_history(document_id, question, answer):
    safe_question = sanitize_input(question)
    
    db = SessionLocal()
    try:
        chat = ChatHistory(
            document_id=document_id,
            question=safe_question,
            answer=answer
        )
        db.add(chat)
        db.commit()
    finally:
        db.close()


def get_chat_history(document_id=None):
    db = SessionLocal()
    try:
        if document_id:
            history = db.query(ChatHistory).filter(ChatHistory.document_id == document_id).order_by(ChatHistory.timestamp.desc()).all()
        else:
            history = db.query(ChatHistory).order_by(ChatHistory.timestamp.desc()).all()
        return history
    finally:
        db.close()


def get_all_tags():
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        return tags
    finally:
        db.close()


def create_tag(name, color="#6366F1"):
    safe_name = sanitize_input(name)
    if not safe_name or len(safe_name) > 50:
        return None
        
    db = SessionLocal()
    try:
        existing = db.query(Tag).filter(Tag.name == safe_name).first()
        if existing:
            return existing.id
        tag = Tag(name=safe_name, color=color)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag.id
    finally:
        db.close()


def add_tag_to_document(doc_id, tag_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if document and tag:
            if tag not in document.tags:
                document.tags.append(tag)
                db.commit()
            return True
        return False
    finally:
        db.close()


def remove_tag_from_document(doc_id, tag_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if document and tag and tag in document.tags:
            document.tags.remove(tag)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_document_tags(doc_id):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            return list(document.tags)
        return []
    finally:
        db.close()


def update_document_category(doc_id, category):
    safe_category = sanitize_input(category) if category else None
    
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.category = safe_category
            db.commit()
            return True
        return False
    finally:
        db.close()


def search_documents(query):
    safe_query, warnings = validate_search_query(query)
    if not safe_query:
        return []
    
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(
            Document.extracted_text.ilike(f"%{safe_query}%") | 
            Document.filename.ilike(f"%{safe_query}%")
        ).all()
        return documents
    finally:
        db.close()


def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def export_chat_history(document_id=None, format_type="json"):
    history = get_chat_history(document_id)
    
    if format_type == "json":
        data = []
        for chat in history:
            doc = get_document_by_id(chat.document_id) if chat.document_id else None
            data.append({
                "document": sanitize_for_display(doc.filename) if doc else "All Documents",
                "question": sanitize_for_display(chat.question),
                "answer": sanitize_for_display(chat.answer),
                "timestamp": chat.timestamp.isoformat()
            })
        return json.dumps(data, indent=2)
    else:
        lines = []
        for chat in history:
            doc = get_document_by_id(chat.document_id) if chat.document_id else None
            lines.append(f"Document: {sanitize_for_display(doc.filename) if doc else 'All Documents'}")
            lines.append(f"Time: {chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Q: {sanitize_for_display(chat.question)}")
            lines.append(f"A: {sanitize_for_display(chat.answer)}")
            lines.append("-" * 50)
        return "\n".join(lines)


if REQUIRE_AUTH and APP_PASSWORD_HASH and not check_authentication():
    show_login_page()
    st.stop()

st.markdown('<h1 style="text-align: center;">📄 <span class="header-gradient">PDF Document Assistant</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748B; margin-bottom: 2rem;">Upload PDFs and ask questions about your documents using AI <span class="security-badge">🔒 Secured</span></p>', unsafe_allow_html=True)

if not is_api_configured():
    st.warning("⚠️ AI features are disabled. Please configure your GEMINI_API_KEY in the Secrets tab to enable AI-powered Q&A.")

with st.sidebar:
    if REQUIRE_AUTH and APP_PASSWORD_HASH:
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.authenticated = False
            log_security_event("LOGOUT", "User logged out", st.session_state.client_id)
            st.rerun()
        st.markdown("---")
    
    st.markdown("### 🔍 Search Documents")
    search_query = st.text_input("Search in documents...", value=st.session_state.search_query, key="search_input")
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
    
    st.markdown("---")
    
    st.markdown("### 🏷️ Tags & Categories")
    
    all_tags = get_all_tags()
    if all_tags:
        st.markdown("**Existing Tags:**")
        for tag in all_tags:
            st.markdown(f'<span class="tag-badge" style="background-color: {sanitize_for_display(tag.color)}; color: white;">{sanitize_for_display(tag.name)}</span>', unsafe_allow_html=True)
    
    with st.expander("➕ Create New Tag"):
        new_tag_name = st.text_input("Tag name", key="new_tag_name", max_chars=50)
        tag_colors = ["#6366F1", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444", "#06B6D4", "#EC4899"]
        new_tag_color = st.selectbox("Tag color", tag_colors, format_func=lambda x: f"● {x}")
        if st.button("Create Tag"):
            if new_tag_name:
                tag_id = create_tag(new_tag_name, new_tag_color)
                if tag_id:
                    st.success(f"Tag created!")
                    st.rerun()
                else:
                    st.error("Failed to create tag. Name may be invalid or too long.")
    
    st.markdown("---")
    
    st.markdown("### 📊 Compare Documents")
    documents = get_all_documents()
    if len(documents) >= 2:
        doc_options = {doc.id: sanitize_for_display(doc.filename) for doc in documents}
        selected_for_compare = st.multiselect(
            "Select documents to compare",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options[x],
            max_selections=3
        )
        st.session_state.compare_docs = selected_for_compare
        
        if len(selected_for_compare) >= 2:
            if st.button("🔄 Compare Selected"):
                st.session_state.view_mode = "compare"
                st.session_state.all_documents_mode = False
                st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📤 Export")
    if st.button("Export Chat History (JSON)"):
        export_data = export_chat_history(format_type="json")
        st.download_button(
            label="Download JSON",
            data=export_data,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    if st.button("Export Chat History (Text)"):
        export_data = export_chat_history(format_type="text")
        st.download_button(
            label="Download Text",
            data=export_data,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if st.session_state.search_query:
    documents = search_documents(st.session_state.search_query)
else:
    documents = get_all_documents()

left_col, right_col = st.columns([1, 1.5], gap="large")

with left_col:
    st.markdown("### 📤 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Drag and drop a PDF file here",
        type=["pdf"],
        help="Supports both regular and scanned PDFs (max 50MB)"
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_size = len(file_bytes)
        
        is_valid, validation_errors = validate_pdf_file(file_bytes, uploaded_file.name)
        
        if not is_valid:
            for error in validation_errors:
                st.error(f"⚠️ {error}")
            log_security_event("UPLOAD_REJECTED", f"File: {uploaded_file.name}, Errors: {validation_errors}", st.session_state.client_id)
        else:
            existing_docs = get_all_documents()
            existing_names = [doc.filename for doc in existing_docs]
            safe_filename = sanitize_filename(uploaded_file.name)
            
            if safe_filename not in existing_names:
                with st.spinner("Processing PDF... This may take a moment for scanned documents."):
                    try:
                        extracted_text, page_count, is_scanned = extract_text_from_pdf(file_bytes)
                        
                        doc_id = save_document(
                            filename=safe_filename,
                            file_data=file_bytes,
                            extracted_text=extracted_text,
                            page_count=page_count,
                            file_size=file_size,
                            is_scanned=is_scanned
                        )
                        
                        st.session_state.selected_document = doc_id
                        st.session_state.current_page = 1
                        
                        if is_scanned:
                            st.success(f"✅ Scanned PDF uploaded successfully! Extracted text using OCR.")
                        else:
                            st.success(f"✅ PDF uploaded and processed successfully!")
                        
                        st.rerun()
                        
                    except Exception as e:
                        log_security_event("UPLOAD_ERROR", f"File: {safe_filename}, Error: {str(e)}", st.session_state.client_id)
                        st.error(f"Failed to process PDF: Please ensure the file is a valid PDF document.")
            else:
                st.info("This document has already been uploaded.")
    
    st.markdown("---")
    st.markdown("### 📚 Document Library")
    
    if st.session_state.search_query:
        st.markdown(f"*Showing results for: \"{sanitize_for_display(st.session_state.search_query)}\"*")
    
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
                
                doc_tags = get_document_tags(doc.id)
                tags_html = ""
                for tag in doc_tags:
                    tags_html += f'<span class="tag-badge" style="background-color: {sanitize_for_display(tag.color)}; color: white;">{sanitize_for_display(tag.name)}</span>'
                
                category_text = f" • {sanitize_for_display(doc.category)}" if doc.category else ""
                
                card_class = "document-card selected" if is_selected else "document-card"
                
                st.markdown(f'''
                <div class="{card_class}">
                    <div class="document-title">📄 {sanitize_for_display(doc.filename)} {badge}</div>
                    <div class="document-meta">{doc.page_count} pages • {format_file_size(doc.file_size)} • {doc.upload_date.strftime("%b %d, %Y")}{category_text}</div>
                    <div>{tags_html}</div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"Select", key=f"select_{doc.id}", use_container_width=True):
                    st.session_state.selected_document = doc.id
                    st.session_state.all_documents_mode = False
                    st.session_state.messages = []
                    st.session_state.current_page = 1
                    st.session_state.view_mode = "chat"
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{doc.id}", help="Delete document"):
                    if delete_document(doc.id):
                        if st.session_state.selected_document == doc.id:
                            st.session_state.selected_document = None
                            st.session_state.messages = []
                        st.rerun()
    else:
        if st.session_state.search_query:
            st.info("No documents match your search query.")
        else:
            st.info("No documents uploaded yet. Upload your first PDF to get started!")

with right_col:
    if st.session_state.selected_document and st.session_state.view_mode != "compare":
        view_tabs = st.tabs(["💬 Chat", "👁️ View PDF", "🏷️ Tags & Category"])
        
        with view_tabs[0]:
            st.markdown("### 💬 Chat with Documents")
            
            if st.session_state.all_documents_mode:
                st.markdown('<div style="background: #F5F3FF; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;"><span style="color: #6366F1; font-weight: 500;">🔍 Searching across all documents</span></div>', unsafe_allow_html=True)
                context_docs = get_all_documents()
                combined_context = ""
                for doc in context_docs:
                    if doc.extracted_text:
                        combined_context += f"\n\n--- Document: {sanitize_for_display(doc.filename)} ---\n{doc.extracted_text}"
                document_context = combined_context
                current_doc_name = "All Documents"
                current_doc_id = None
            else:
                current_doc = get_document_by_id(st.session_state.selected_document)
                if current_doc:
                    st.markdown(f'<div style="background: #F5F3FF; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;"><span style="color: #6366F1; font-weight: 500;">📄 Chatting with: {sanitize_for_display(current_doc.filename)}</span></div>', unsafe_allow_html=True)
                    document_context = current_doc.extracted_text
                    current_doc_name = current_doc.filename
                    current_doc_id = current_doc.id
                else:
                    document_context = None
                    current_doc_name = None
                    current_doc_id = None
            
            chat_container = st.container()
            
            with chat_container:
                if st.session_state.messages:
                    for message in st.session_state.messages:
                        if message["role"] == "user":
                            st.markdown(f'<div class="message-user">{sanitize_for_display(message["content"])}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="message-assistant">{sanitize_for_display(message["content"])}</div>', unsafe_allow_html=True)
                elif document_context:
                    st.markdown("""
                    <div style="text-align: center; padding: 2rem; color: #64748B;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">💭</div>
                        <p>Ask any question about your document!</p>
                        <p style="font-size: 0.85rem;">Try: "What is this document about?" or "Summarize the key points"</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if document_context:
                col_input, col_btn = st.columns([5, 1])
                
                with col_input:
                    user_question = st.text_input(
                        "Ask a question",
                        placeholder="Type your question here...",
                        key="user_input",
                        label_visibility="collapsed",
                        max_chars=1000
                    )
                
                with col_btn:
                    send_button = st.button("Send", use_container_width=True)
                
                col_summary, col_clear = st.columns(2)
                
                with col_summary:
                    if st.button("📝 Summarize Document", use_container_width=True):
                        can_proceed, rate_error = check_rate_limit(st.session_state.client_id, "ai_request")
                        if not can_proceed:
                            st.error(rate_error)
                        else:
                            with st.spinner("Generating summary..."):
                                summary = summarize_document(str(document_context), str(current_doc_name) if current_doc_name else None)
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
                    safe_question = sanitize_input(user_question)
                    
                    can_proceed, rate_error = check_rate_limit(st.session_state.client_id, "ai_request")
                    if not can_proceed:
                        st.error(rate_error)
                    else:
                        st.session_state.messages.append({"role": "user", "content": safe_question})
                        
                        with st.spinner("Thinking..."):
                            answer = answer_question(safe_question, str(document_context), str(current_doc_name) if current_doc_name else None)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                            
                            if current_doc_id:
                                save_chat_history(current_doc_id, safe_question, answer)
                        
                        st.rerun()
        
        with view_tabs[1]:
            st.markdown("### 👁️ PDF Viewer")
            
            current_doc = get_document_by_id(st.session_state.selected_document)
            if current_doc and current_doc.file_data:
                col_nav1, col_page, col_nav2, col_zoom = st.columns([1, 2, 1, 2])
                
                with col_nav1:
                    if st.button("◀ Prev", use_container_width=True):
                        if st.session_state.current_page > 1:
                            st.session_state.current_page -= 1
                            st.rerun()
                
                with col_page:
                    st.markdown(f"<div style='text-align: center; padding: 0.5rem;'>Page {st.session_state.current_page} of {current_doc.page_count}</div>", unsafe_allow_html=True)
                
                with col_nav2:
                    if st.button("Next ▶", use_container_width=True):
                        if st.session_state.current_page < current_doc.page_count:
                            st.session_state.current_page += 1
                            st.rerun()
                
                with col_zoom:
                    zoom = st.select_slider("Zoom", options=[50, 75, 100, 125, 150, 200], value=st.session_state.zoom_level)
                    if zoom != st.session_state.zoom_level:
                        st.session_state.zoom_level = zoom
                
                with st.spinner("Loading page..."):
                    dpi = int(150 * (st.session_state.zoom_level / 100))
                    page_image = get_pdf_page_as_image(bytes(current_doc.file_data), st.session_state.current_page, dpi=dpi)
                    
                    if page_image:
                        st.markdown(f'<div class="pdf-viewer-container"><img src="{page_image}" style="max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>', unsafe_allow_html=True)
                    else:
                        st.error("Failed to render page. The PDF might be corrupted.")
                
                page_jump = st.number_input("Go to page", min_value=1, max_value=int(current_doc.page_count), value=st.session_state.current_page)
                if page_jump != st.session_state.current_page:
                    st.session_state.current_page = page_jump
                    st.rerun()
        
        with view_tabs[2]:
            st.markdown("### 🏷️ Tags & Category")
            
            current_doc = get_document_by_id(st.session_state.selected_document)
            if current_doc:
                st.markdown(f"**Document:** {sanitize_for_display(current_doc.filename)}")
                
                categories = ["", "Work", "Personal", "Research", "Legal", "Financial", "Medical", "Educational", "Other"]
                current_category = current_doc.category if current_doc.category else ""
                selected_category = st.selectbox("Category", categories, index=categories.index(current_category) if current_category in categories else 0)
                
                if selected_category != current_category:
                    update_document_category(current_doc.id, selected_category if selected_category else None)
                    st.success("Category updated!")
                    st.rerun()
                
                st.markdown("---")
                st.markdown("**Tags:**")
                
                current_tags = get_document_tags(current_doc.id)
                all_tags = get_all_tags()
                
                if current_tags:
                    for tag in current_tags:
                        col_tag, col_remove = st.columns([4, 1])
                        with col_tag:
                            st.markdown(f'<span class="tag-badge" style="background-color: {sanitize_for_display(tag.color)}; color: white;">{sanitize_for_display(tag.name)}</span>', unsafe_allow_html=True)
                        with col_remove:
                            if st.button("✕", key=f"remove_tag_{tag.id}"):
                                remove_tag_from_document(current_doc.id, tag.id)
                                st.rerun()
                else:
                    st.info("No tags assigned to this document.")
                
                available_tags = [t for t in all_tags if t not in current_tags]
                if available_tags:
                    st.markdown("**Add Tag:**")
                    tag_to_add = st.selectbox("Select tag", options=[None] + available_tags, format_func=lambda x: sanitize_for_display(x.name) if x else "Select a tag...")
                    if tag_to_add:
                        if st.button("Add Tag"):
                            add_tag_to_document(current_doc.id, tag_to_add.id)
                            st.success(f"Tag added!")
                            st.rerun()
    
    elif st.session_state.view_mode == "compare" and len(st.session_state.compare_docs) >= 2:
        st.markdown("### 📊 Document Comparison")
        
        compare_docs_data = [get_document_by_id(doc_id) for doc_id in st.session_state.compare_docs]
        compare_docs_data = [d for d in compare_docs_data if d]
        
        if len(compare_docs_data) >= 2:
            st.markdown(f"**Comparing {len(compare_docs_data)} documents:**")
            for doc in compare_docs_data:
                st.markdown(f"- {sanitize_for_display(doc.filename)}")
            
            st.markdown("---")
            
            if st.button("🔍 Generate Comparative Analysis", use_container_width=True):
                can_proceed, rate_error = check_rate_limit(st.session_state.client_id, "ai_request")
                if not can_proceed:
                    st.error(rate_error)
                else:
                    combined_context = ""
                    for doc in compare_docs_data:
                        if doc.extracted_text:
                            combined_context += f"\n\n=== Document: {sanitize_for_display(doc.filename)} ===\n{doc.extracted_text[:10000]}"
                    
                    with st.spinner("Analyzing documents..."):
                        analysis = answer_question(
                            "Please provide a detailed comparison of these documents. Include: 1) Key similarities 2) Main differences 3) Unique points from each document 4) Overall summary",
                            combined_context,
                            "Multiple Documents"
                        )
                        st.markdown("#### Analysis Results:")
                        st.markdown(sanitize_for_display(analysis))
            
            user_compare_question = st.text_input("Ask a question about these documents...", key="compare_question", max_chars=1000)
            if st.button("Ask", key="compare_ask") and user_compare_question:
                can_proceed, rate_error = check_rate_limit(st.session_state.client_id, "ai_request")
                if not can_proceed:
                    st.error(rate_error)
                else:
                    safe_question = sanitize_input(user_compare_question)
                    combined_context = ""
                    for doc in compare_docs_data:
                        if doc.extracted_text:
                            combined_context += f"\n\n=== Document: {sanitize_for_display(doc.filename)} ===\n{doc.extracted_text}"
                    
                    with st.spinner("Thinking..."):
                        answer = answer_question(safe_question, combined_context, "Multiple Documents")
                        st.markdown("#### Answer:")
                        st.markdown(sanitize_for_display(answer))
            
            if st.button("← Back to Chat"):
                st.session_state.view_mode = "chat"
                st.rerun()
    
    else:
        st.markdown("### 💬 Chat with Documents")
        
        if st.session_state.all_documents_mode:
            st.markdown('<div style="background: #F5F3FF; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;"><span style="color: #6366F1; font-weight: 500;">🔍 Searching across all documents</span></div>', unsafe_allow_html=True)
            context_docs = get_all_documents()
            combined_context = ""
            for doc in context_docs:
                if doc.extracted_text:
                    combined_context += f"\n\n--- Document: {sanitize_for_display(doc.filename)} ---\n{doc.extracted_text}"
            document_context = combined_context
            current_doc_name = "All Documents"
            current_doc_id = None
            
            chat_container = st.container()
            
            with chat_container:
                if st.session_state.messages:
                    for message in st.session_state.messages:
                        if message["role"] == "user":
                            st.markdown(f'<div class="message-user">{sanitize_for_display(message["content"])}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="message-assistant">{sanitize_for_display(message["content"])}</div>', unsafe_allow_html=True)
                elif document_context:
                    st.markdown("""
                    <div style="text-align: center; padding: 2rem; color: #64748B;">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">💭</div>
                        <p>Ask any question about your documents!</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if document_context:
                col_input, col_btn = st.columns([5, 1])
                
                with col_input:
                    user_question = st.text_input(
                        "Ask a question",
                        placeholder="Type your question here...",
                        key="user_input_all",
                        label_visibility="collapsed",
                        max_chars=1000
                    )
                
                with col_btn:
                    send_button = st.button("Send", use_container_width=True, key="send_all")
                
                if send_button and user_question:
                    safe_question = sanitize_input(user_question)
                    
                    can_proceed, rate_error = check_rate_limit(st.session_state.client_id, "ai_request")
                    if not can_proceed:
                        st.error(rate_error)
                    else:
                        st.session_state.messages.append({"role": "user", "content": safe_question})
                        
                        with st.spinner("Thinking..."):
                            answer = answer_question(safe_question, str(document_context), current_doc_name)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        
                        st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #64748B;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                <p>Upload a document or select one from your library to start chatting!</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #94A3B8; font-size: 0.85rem;">PDF Document Assistant • Powered by AI • 🔒 Secured</p>',
    unsafe_allow_html=True
)
