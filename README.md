# PDF OCR and Text Extraction for Arabic Documents

Extract text from Arabic legal documents using different methods and formats.

## Quick Start

```bash
make install
make help  # See all available commands
```

## Makefile Commands (Recommended)

### Batch Processing (All PDFs in `data/`)
```bash
make process-smart                # Smart OCR detection (Recommended)
make process-fast                 # Fast text extraction (PyMuPDF)
make process-paddle               # PaddleOCR processing
make process-tesseract            # Tesseract OCR processing
make process-structured           # Enhanced structured output
make process-smart-structured     # Smart + structured output
```

### Single File Processing
```bash
make process-single-fast FILE="path/to/file.pdf"
make process-single-paddle FILE="path/to/file.pdf"
make process-single-tesseract FILE="path/to/file.pdf"
```

## Direct Script Usage

### Single File Processing
```bash
python scripts/pdfplumber-to-json.py "pdfs/document.pdf"     # Fast text extraction
python scripts/paddle-to-json.py "pdfs/document.pdf"        # PaddleOCR
python scripts/tesseract-to-json.py "pdfs/document.pdf"     # Tesseract
```

### Batch Processing
```bash
python scripts/all-pdf-to-json-smart.py                     # Smart OCR detection
python scripts/all-pdf-to-json-pdfplumber.py               # Fast (text-based)
python scripts/all-pdf-to-json-paddle.py                   # PaddleOCR
python scripts/all-pdf-to-json-tesseract.py                # Tesseract
python scripts/all-pdf-to-json-structured.py               # Enhanced metadata
python scripts/all-pdf-to-json-smart-structured.py         # Smart + structured
```

## Output Formats

**Simple:** `{filename, text}`  
**Structured:** `{metadata, document_info, content, analysis}`

## Processing Methods

- **Smart Detection** 🧠 - Automatically detects which pages need OCR
- **PyMuPDF** ⚡ - Fast text extraction for text-based PDFs  
- **PaddleOCR** 🔍 - Advanced OCR for scanned documents
- **Tesseract** 📝 - Alternative OCR engine with Arabic support

## Features
Arabic text normalization • Progress tracking • Smart OCR detection • Directory structure preservation • Comprehensive metadata • Legal document analysis

## Project Structure

```
qaanoon-ai/
├── scripts/                    # All processing scripts
│   ├── pdfplumber-to-json.py   # Single file - fast extraction
│   ├── paddle-to-json.py       # Single file - PaddleOCR
│   ├── tesseract-to-json.py    # Single file - Tesseract
│   ├── all-pdf-to-json-smart.py # Batch - smart OCR detection
│   └── ...                     # Other batch processing scripts
├── data/                       # Input PDF files
├── results/                    # Simple JSON output
├── structured_results/         # Enhanced JSON with metadata
├── hybrid_results/             # Smart processing output
└── Makefile                    # Automation commands
```

```
data/              # Input PDFs (organized by category)
results/           # Simple JSON output  
structured_results/ # Enhanced JSON with metadata
output/            # Single file outputs
```
