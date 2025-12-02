# PDF Document Assistant

## Overview
A secure web-based PDF document management and AI-powered Q&A application that allows users to upload scanned PDFs or regular PDFs, stores them in a PostgreSQL database, and provides intelligent question-answering capabilities based on the document content.

## Current State
All MVP, next-phase features, and security enhancements are complete:

### Core Features (MVP)
- PDF upload with drag-and-drop support
- Text extraction from regular PDFs (PyPDF2) and scanned PDFs (OCR via Tesseract)
- PostgreSQL database storage for documents and extracted text
- Document library with metadata display
- AI-powered Q&A using Google Gemini (free tier)
- Two-panel layout with indigo/purple color scheme
- Chat interface with history

### Advanced Features (Next Phase)
- PDF viewer with page navigation and zoom controls
- Document tagging and categorization system
- Advanced search with keyword filtering across documents
- Export functionality for chat history (JSON and Text formats)
- Multi-document comparative analysis and cross-reference capabilities

### Security Features
- **Password Authentication**: Optional password protection for the entire app
- **Input Sanitization**: All user inputs are sanitized to prevent XSS attacks
- **File Validation**: PDF files are validated for size, format, and magic bytes
- **Rate Limiting**: AI requests are rate-limited (20 requests per minute)
- **Security Logging**: All security events are logged (uploads, logins, deletions)
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Secure Session Management**: Unique client identifiers for tracking

## Project Structure
```
/
├── app.py              # Main Streamlit application with UI
├── models.py           # SQLAlchemy database models (Document, ChatHistory, Tag)
├── gemini_ai.py        # Gemini AI integration for Q&A and summarization
├── pdf_processor.py    # PDF text extraction and OCR processing
├── pdf_viewer.py       # PDF page rendering for inline viewing
├── security.py         # Security utilities (auth, sanitization, validation)
├── .streamlit/
│   └── config.toml     # Streamlit server configuration
└── pyproject.toml      # Python dependencies
```

## Key Components

### Security Module (security.py)
- `sanitize_input()`: Escapes HTML and removes dangerous patterns
- `sanitize_filename()`: Cleans filenames to prevent path traversal
- `validate_pdf_file()`: Validates PDF magic bytes, size limits, format
- `check_rate_limit()`: Rate limits API requests per client
- `hash_password()` / `verify_password()`: Secure password handling with PBKDF2
- `log_security_event()`: Logs security-related events

### Database Models (models.py)
- `Document`: Stores PDF files, extracted text, metadata
- `ChatHistory`: Stores Q&A history per document
- `Tag`: Stores custom tags with colors
- `document_tags`: Many-to-many relationship table

### AI Integration (gemini_ai.py)
- Uses Google Gemini 2.5 Flash model
- `answer_question()`: Answers questions based on document context
- `summarize_document()`: Generates document summaries
- `is_api_configured()`: Checks if API key is available

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)
- `GEMINI_API_KEY`: Google Gemini API key (required for AI features)
- `SESSION_SECRET`: Secret key for session security (auto-generated if not set)
- `APP_PASSWORD_HASH`: Hashed password for app access (optional)
- `REQUIRE_AUTH`: Set to "false" to disable authentication (default: "true")

## Setting Up Password Protection
To enable password protection:

1. Generate a password hash using Python:
```python
from security import hash_password
print(hash_password("your_secure_password"))
```

2. Add the hash to your Secrets as `APP_PASSWORD_HASH`

3. Set `REQUIRE_AUTH=true` in your environment

## Running the Application
```
streamlit run app.py --server.port 5000
```

## Style Guide
- Primary: #6366F1 (indigo)
- Secondary: #8B5CF6 (purple)
- Background: #F8FAFC (light grey)
- Text: #1E293B (slate)
- Accent: #10B981 (emerald)
- Document: #FFFFFF (white)
- Font: Inter/system fonts

## Security Limits
- Max file size: 50MB
- Max question length: 1000 characters
- Max tag name length: 50 characters
- Rate limit: 20 AI requests per minute
- Login attempts: 5 before lockout

## User Interface
- **Left Panel**: Upload area, document library with stats, document cards with tags
- **Right Panel**: Tabbed interface with Chat, PDF Viewer, and Tags/Category management
- **Sidebar**: Search, tag management, document comparison, export options, logout button

## Recent Changes
- November 26, 2025: Initial MVP build with all core features
- November 26, 2025: Added PDF viewer with page navigation and zoom
- November 26, 2025: Added tagging and categorization system
- November 26, 2025: Added document search functionality
- November 26, 2025: Added chat history export (JSON/Text)
- November 26, 2025: Added multi-document comparison feature
- December 02, 2025: Added comprehensive security features (auth, sanitization, validation, rate limiting)
