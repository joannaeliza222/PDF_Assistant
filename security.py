import os
import re
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
import html

SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf'}
PDF_MAGIC_BYTES = b'%PDF'

rate_limit_store = {}
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60


def sanitize_input(text):
    if text is None:
        return None
    if not isinstance(text, str):
        return str(text)
    sanitized = html.escape(text)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def sanitize_filename(filename):
    if not filename:
        return "document.pdf"
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = re.sub(r'\.\.+', '.', sanitized)
    sanitized = sanitized.strip('. ')
    if not sanitized:
        return "document.pdf"
    if not sanitized.lower().endswith('.pdf'):
        sanitized += '.pdf'
    if len(sanitized) > 255:
        sanitized = sanitized[:250] + '.pdf'
    return sanitized


def validate_pdf_file(file_bytes, filename):
    errors = []
    
    if len(file_bytes) > MAX_FILE_SIZE:
        errors.append(f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB")
    
    if len(file_bytes) < 4:
        errors.append("File is too small to be a valid PDF")
        return False, errors
    
    if not file_bytes[:4] == PDF_MAGIC_BYTES:
        errors.append("File does not appear to be a valid PDF (invalid header)")
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        errors.append(f"File extension '{ext}' is not allowed. Only PDF files are accepted.")
    
    dangerous_patterns = [
        (b'/JavaScript', "executable JavaScript code"),
        (b'/JS ', "JavaScript reference"),
        (b'/Launch', "external application launch action"),
        (b'/EmbeddedFile', "embedded executable file"),
        (b'/OpenAction', "automatic action on open"),
        (b'/AA ', "automatic trigger actions"),
        (b'/XFA', "XFA form with active content"),
        (b'/RichMedia', "rich media content"),
        (b'/Sound', "embedded audio"),
        (b'/Movie', "embedded video"),
    ]
    
    detected_threats = []
    for pattern, description in dangerous_patterns:
        if pattern in file_bytes:
            detected_threats.append(description)
    
    if detected_threats:
        log_security_event("PDF_REJECTED_SECURITY", f"File: {filename}, Threats: {detected_threats}")
        errors.append(f"PDF rejected: contains potentially dangerous content ({', '.join(detected_threats[:3])})")
    
    return len(errors) == 0, errors


def check_rate_limit(user_id, action="api_call"):
    key = f"{user_id}:{action}"
    current_time = time.time()
    
    if key not in rate_limit_store:
        rate_limit_store[key] = []
    
    rate_limit_store[key] = [
        t for t in rate_limit_store[key] 
        if current_time - t < RATE_LIMIT_WINDOW
    ]
    
    if len(rate_limit_store[key]) >= RATE_LIMIT_REQUESTS:
        return False, f"Rate limit exceeded. Please wait before making more requests."
    
    rate_limit_store[key].append(current_time)
    return True, None


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        (salt + SESSION_SECRET).encode('utf-8'),
        100000
    )
    return f"{salt}${hashed.hex()}"


def verify_password(password, stored_hash):
    try:
        salt, hashed = stored_hash.split('$')
        new_hash = hash_password(password, salt)
        return secrets.compare_digest(new_hash, stored_hash)
    except (ValueError, AttributeError):
        return False


def generate_session_token():
    return secrets.token_urlsafe(32)


def validate_session_token(token):
    if not token or not isinstance(token, str):
        return False
    if len(token) < 32:
        return False
    return True


def sanitize_for_display(text, max_length=None):
    if text is None:
        return ""
    sanitized = html.escape(str(text))
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    return sanitized


def log_security_event(event_type, details, user_id=None):
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"[{timestamp}] [{event_type}]"
    if user_id:
        log_entry += f" [User: {user_id}]"
    log_entry += f" {details}"
    print(log_entry)


def validate_search_query(query):
    if not query:
        return "", []
    
    sanitized = sanitize_input(query)
    
    sql_patterns = [
        r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b',
        r'--',
        r';',
        r"'.*OR.*'",
    ]
    
    warnings = []
    for pattern in sql_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
            warnings.append("Potentially unsafe characters were removed from your search")
    
    return sanitized.strip(), warnings


def get_client_identifier(existing_id=None):
    if existing_id and isinstance(existing_id, str) and len(existing_id) >= 16:
        return existing_id
    return secrets.token_hex(8)


def sanitize_extracted_text(text):
    if not text:
        return ""
    sanitized = html.escape(str(text))
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'data:\s*text/html', '', sanitized, flags=re.IGNORECASE)
    return sanitized
