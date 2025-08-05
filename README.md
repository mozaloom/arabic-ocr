# Qaanoon AI - PDF Text Extraction Tools

Simple tools for extracting text from Arabic legal documents using different OCR engines.

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Usage

Choose the extraction method that works best for your documents:

#### 1. Fast Text Extraction (Recommended for text-based PDFs)
```bash
python pdfplumber-to-json.py "pdfs/document.pdf"
```

#### 2. PaddleOCR (Best for Arabic scanned documents)
```bash
python paddle-to-json.py "pdfs/document.pdf"
```

#### 3. Tesseract OCR (Alternative OCR engine)
```bash
python tesseract-to-json.py "pdfs/document.pdf"
```

### Output

All extracted text is saved as JSON files in the `output/` directory:
```json
{
  "filename": "document.pdf",
  "text": "Extracted Arabic text content..."
}
```

### Features

- ✅ Arabic text processing and normalization
- ⏱️ Real-time progress tracking with timers
- 📁 Organized output in dedicated directory
- 🔄 Page-by-page processing feedback
- 📊 Character count and processing statistics

### File Structure

```
pdfs/           # Input PDF files
output/         # Generated JSON files
src/           # Core processing modules
```

That's it! The tools handle Arabic text normalization and provide detailed progress feedback automatically.
