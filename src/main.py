# Main entry point for the text extraction application
from utils.file_handler import detect_pdf_type

print(detect_pdf_type("pdfs/نظام الإثبات.pdf"))
# Expect "text" or "scanned"
