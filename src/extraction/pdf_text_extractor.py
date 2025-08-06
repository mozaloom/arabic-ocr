# src/extraction/image_text_extractor.py

import fitz  # PyMuPDF
import easyocr
from typing import List

class ScannedPDFExtractor:
    """Extract text from scanned/image-based PDFs using EasyOCR."""

    def __init__(self, lang: str = "ar", gpu: bool = False):
        """
        Args:
            lang: language code(s) for EasyOCR, e.g. ["ar"] or ["ar","en"].
            gpu: whether to use GPU (if available).
        """
        self.reader = easyocr.Reader([lang], gpu=gpu)

    def extract_text(
        self,
        pdf_path: str,
        pages: List[int] = None,
        dpi: int = 300
    ) -> List[str]:
        """
        Renders pages to images and runs OCR.

        Args:
            pdf_path: path to the PDF file.
            pages: list of 0-based page indices to process (None = all).
            dpi: rendering resolution for clarity (higher → slower).

        Returns:
            List of strings (one per page).
        """
        texts: List[str] = []
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        page_indices = pages if pages is not None else list(range(total_pages))

        for i in page_indices:
            page = doc[i]
            # Render page to a PNG-format pixmap in memory
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")

            # Run EasyOCR
            ocr_result = self.reader.readtext(img_bytes, detail=0)
            # detail=0 returns only the text strings in reading order
            page_text = "\n".join(ocr_result)
            texts.append(page_text)

        return texts
