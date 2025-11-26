import io
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, int, bool]:
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        page_count = len(reader.pages)
        
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n\n"
        
        extracted_text = extracted_text.strip()
        
        if len(extracted_text) < 50:
            ocr_text, is_scanned = extract_text_with_ocr(pdf_bytes)
            if ocr_text and len(ocr_text) > len(extracted_text):
                return ocr_text, page_count, True
        
        return extracted_text, page_count, False
    
    except Exception as e:
        try:
            ocr_text, is_scanned = extract_text_with_ocr(pdf_bytes)
            if ocr_text:
                pdf_file = io.BytesIO(pdf_bytes)
                try:
                    reader = PdfReader(pdf_file)
                    page_count = len(reader.pages)
                except:
                    page_count = 1
                return ocr_text, page_count, True
        except:
            pass
        
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_with_ocr(pdf_bytes: bytes) -> tuple[str, bool]:
    try:
        images = convert_from_bytes(pdf_bytes, dpi=200)
        
        extracted_text = ""
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            if text.strip():
                extracted_text += f"--- Page {i + 1} ---\n{text}\n\n"
        
        return extracted_text.strip(), True
    
    except Exception as e:
        raise Exception(f"OCR extraction failed: {str(e)}")


def get_pdf_info(pdf_bytes: bytes) -> dict:
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        info = {
            "page_count": len(reader.pages),
            "metadata": {},
            "file_size": len(pdf_bytes)
        }
        
        if reader.metadata:
            info["metadata"] = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
            }
        
        return info
    
    except Exception as e:
        return {
            "page_count": 0,
            "metadata": {},
            "file_size": len(pdf_bytes),
            "error": str(e)
        }
