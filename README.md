# Qaanoon AI - PDF Text Extraction Tools

Extract text from Arabic legal documents using different methods and formats.

## Quick Start

```bash
pip install -r requirements.txt
```

## Single File Processing

#### Fast Text Extraction (text-based PDFs)
```bash
python pdfplumber-to-json.py "pdfs/document.pdf"
```

#### OCR Processing (scanned documents)
```bash
python paddle-to-json.py "pdfs/document.pdf"     # PaddleOCR
python tesseract-to-json.py "pdfs/document.pdf"  # Tesseract
```

## Batch Processing

#### Smart Processing
```bash
python all-pdf-to-json-smart.py
```
*Auto-detects OCR needs per page. Uses fast extraction + OCR fallback*

#### Process All Files by Method
```bash
python all-pdf-to-json-pdfplumber.py    # Fast (text-based)
python all-pdf-to-json-paddle.py        # PaddleOCR
python all-pdf-to-json-tesseract.py     # Tesseract
python all-pdf-to-json-structured.py    # Enhanced metadata
```
*All process `data/` → save to `results/`*

## Output Formats

**Simple:** `{filename, text}`  
**Structured:** `{metadata, document_info, content, analysis}`

## Features
Arabic text normalization • Progress tracking • Smart OCR detection • Directory structure preservation

## File Structure

```
data/              # Input PDFs (organized by category)
results/           # Simple JSON output  
structured_results/ # Enhanced JSON with metadata
output/            # Single file outputs
```
