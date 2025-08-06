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

#### Process All Files (Simple Format)
```bash
python all-pdf-to-json-pdfplumber.py
```
*Processes all PDFs in `data/` → saves to `results/`*

#### Process All Files (Structured Format)
```bash
python all-pdf-to-json-structured.py
```
*Processes all PDFs in `data/` → saves to `structured_results/` with enhanced metadata*

## Output Formats

**Simple:** `{filename, text}`  
**Structured:** `{metadata, document_info, content, analysis}`

## Features

✅ Arabic text normalization • ⏱️ Progress tracking • 📁 Directory structure preservation • 📊 Processing statistics

## File Structure

```
data/              # Input PDFs (organized by category)
results/           # Simple JSON output  
structured_results/ # Enhanced JSON with metadata
output/            # Single file outputs
```
