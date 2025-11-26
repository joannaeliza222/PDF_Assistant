# PDF Document Assistant

## Overview
A web-based PDF document management and AI-powered Q&A application that allows users to upload scanned PDFs or regular PDFs, stores them in a PostgreSQL database, and provides intelligent question-answering capabilities based on the document content.

## Current State
All MVP and next-phase features are complete and working:

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

## Project Structure
```
/
├── app.py              # Main Streamlit application with UI
├── models.py           # SQLAlchemy database models (Document, ChatHistory, Tag)
├── gemini_ai.py        # Gemini AI integration for Q&A and summarization
├── pdf_processor.py    # PDF text extraction and OCR processing
├── pdf_viewer.py       # PDF page rendering for inline viewing
├── .streamlit/
│   └── config.toml     # Streamlit server configuration
└── pyproject.toml      # Python dependencies
```

## Key Components

### Database Models (models.py)
- `Document`: Stores PDF files, extracted text, metadata (filename, page_count, file_size, is_scanned, category)
- `ChatHistory`: Stores Q&A history per document
- `Tag`: Stores custom tags with colors
- `document_tags`: Many-to-many relationship table

### AI Integration (gemini_ai.py)
- Uses Google Gemini 2.5 Flash model
- `answer_question()`: Answers questions based on document context
- `summarize_document()`: Generates document summaries
- `is_api_configured()`: Checks if API key is available
- Gracefully handles missing API key

### PDF Processing (pdf_processor.py)
- `extract_text_from_pdf()`: Extracts text from regular PDFs
- `extract_text_with_ocr()`: Uses Tesseract OCR for scanned PDFs
- Auto-detects if OCR is needed based on extracted text quality

### PDF Viewer (pdf_viewer.py)
- `get_pdf_page_as_image()`: Renders a PDF page as base64 image
- `get_pdf_page_count()`: Gets total page count
- `get_pdf_thumbnail()`: Generates thumbnails for document cards

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)
- `GEMINI_API_KEY`: Google Gemini API key (required for AI features)

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

## User Interface
- **Left Panel**: Upload area, document library with stats, document cards with tags
- **Right Panel**: Tabbed interface with Chat, PDF Viewer, and Tags/Category management
- **Sidebar**: Search, tag management, document comparison, export options

## Recent Changes
- November 26, 2025: Initial MVP build with all core features
- November 26, 2025: Added PDF viewer with page navigation and zoom
- November 26, 2025: Added tagging and categorization system
- November 26, 2025: Added document search functionality
- November 26, 2025: Added chat history export (JSON/Text)
- November 26, 2025: Added multi-document comparison feature
