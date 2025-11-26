# PDF Document Assistant

## Overview
A web-based PDF document management and AI-powered Q&A application that allows users to upload scanned PDFs or regular PDFs, stores them in a PostgreSQL database, and provides intelligent question-answering capabilities based on the document content.

## Current State
The MVP features are complete and working:
- PDF upload with drag-and-drop support
- Text extraction from regular PDFs (PyPDF2) and scanned PDFs (OCR via Tesseract)
- PostgreSQL database storage for documents and extracted text
- Document library with metadata display
- AI-powered Q&A using Google Gemini (free tier)
- Two-panel layout with indigo/purple color scheme
- Chat interface with history

## Project Structure
```
/
├── app.py              # Main Streamlit application with UI
├── models.py           # SQLAlchemy database models (Document, ChatHistory)
├── gemini_ai.py        # Gemini AI integration for Q&A and summarization
├── pdf_processor.py    # PDF text extraction and OCR processing
├── .streamlit/
│   └── config.toml     # Streamlit server configuration
└── pyproject.toml      # Python dependencies
```

## Key Components

### Database Models (models.py)
- `Document`: Stores PDF files, extracted text, metadata (filename, page_count, file_size, is_scanned)
- `ChatHistory`: Stores Q&A history per document

### AI Integration (gemini_ai.py)
- Uses Google Gemini 2.5 Flash model
- `answer_question()`: Answers questions based on document context
- `summarize_document()`: Generates document summaries
- Gracefully handles missing API key

### PDF Processing (pdf_processor.py)
- `extract_text_from_pdf()`: Extracts text from regular PDFs
- `extract_text_with_ocr()`: Uses Tesseract OCR for scanned PDFs
- Auto-detects if OCR is needed based on extracted text quality

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

## Recent Changes
- November 26, 2025: Initial MVP build with all core features
