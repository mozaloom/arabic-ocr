# Arabic OCR - PDF Text Extraction

Extract Arabic text from PDFs using OCR and text extraction methods.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Single Files
```bash
# Fast extraction (text-based PDFs)
python pdfplumber-to-json.py "document.pdf"

# OCR extraction (scanned documents)  
python paddle-to-json.py "document.pdf"
python tesseract-to-json.py "document.pdf"
```

### Batch Processing
```bash
# Smart processing (auto-detects OCR needs)
python all-pdf-to-json-smart.py

# Batch by method
python all-pdf-to-json-pdfplumber.py    # Fast extraction
python all-pdf-to-json-paddle.py        # PaddleOCR  
python all-pdf-to-json-tesseract.py     # Tesseract
python all-pdf-to-json-structured.py    # With metadata
```

## Features
- Arabic text normalization
- Multiple OCR engines (PaddleOCR, Tesseract, EasyOCR, TrOCR)
- Smart OCR detection
- Structured output with metadata

## Project Structure

```
├── src/                    # Core modules
│   ├── extraction/         # Text extraction backends
│   ├── ocr/               # OCR implementations  
│   └── utils/             # Utilities & logging
├── all-pdf-to-json-*.py   # Batch processing scripts
├── *-to-json.py          # Single file processors
└── requirements.txt       # Dependencies
```
