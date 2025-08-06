"""
Utility modules for the OCR evaluation framework
"""

from .logger import setup_logger, get_logger
from .file_handler import detect_pdf_type, is_text_pdf

__all__ = ['setup_logger', 'get_logger', 'detect_pdf_type', 'is_text_pdf']
