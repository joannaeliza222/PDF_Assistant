import io
import base64
from pdf2image import convert_from_bytes
from PIL import Image


def get_pdf_page_as_image(pdf_bytes: bytes, page_number: int, dpi: int = 150) -> str:
    try:
        images = convert_from_bytes(
            pdf_bytes, 
            dpi=dpi, 
            first_page=page_number, 
            last_page=page_number
        )
        
        if images:
            img = images[0]
            buffered = io.BytesIO()
            img.save(buffered, format="PNG", optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        return None
    except Exception as e:
        return None


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    try:
        from PyPDF2 import PdfReader
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        return len(reader.pages)
    except Exception:
        return 0


def get_pdf_thumbnail(pdf_bytes: bytes, max_width: int = 200) -> str:
    try:
        images = convert_from_bytes(
            pdf_bytes, 
            dpi=72, 
            first_page=1, 
            last_page=1
        )
        
        if images:
            img = images[0]
            aspect_ratio = img.height / img.width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG", optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        return None
    except Exception:
        return None
