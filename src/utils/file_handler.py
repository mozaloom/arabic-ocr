# File handling utilities
# src/utils/file_handler.py
import pdfplumber
import logging
import warnings

# Suppress pdfminer warnings about PDF parsing issues
logging.getLogger('pdfminer').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=UserWarning, module='pdfminer')

def is_text_pdf(pdf_path: str, page_no: int = 0, char_threshold: int = 20) -> bool:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_no]
        text = page.extract_text() or ""
    return len(text.strip()) >= char_threshold

def detect_pdf_type(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(min(3, len(pdf.pages))):
            text = pdf.pages[i].extract_text() or ""
            if len(text.strip()) >= 20:
                return "text"
        # No page had enough text -> assume scanned
        return "scanned"
