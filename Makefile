install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	python -m pytest -vv test_*.py 

format:
	black *.py scripts/*.py

lint:
	pylint --disable=R,C,E1120 *.py scripts/*.py src/*.py src/**/*.py

help:
	@echo "Available commands:"
	@echo "  install              - Install dependencies"
	@echo "  test                 - Run tests"
	@echo "  format               - Format code with black"
	@echo "  lint                 - Lint code with pylint"
	@echo "  all                  - Install, format, lint, and test"
	@echo ""
	@echo "Batch Processing (all PDFs in data/ directory):"
	@echo "  process-fast         - Fast text extraction (PyMuPDF)"
	@echo "  process-smart        - Smart OCR detection (Recommended)"
	@echo "  process-paddle       - PaddleOCR processing"
	@echo "  process-tesseract    - Tesseract OCR processing"
	@echo "  process-structured   - Enhanced structured output"
	@echo "  process-smart-structured - Smart + structured output"
	@echo ""
	@echo "Single File Processing:"
	@echo "  process-single-fast FILE='path/to/file.pdf'"
	@echo "  process-single-paddle FILE='path/to/file.pdf'"
	@echo "  process-single-tesseract FILE='path/to/file.pdf'"

# Processing commands - Batch processing (all PDFs in data/ directory)
process-fast:
	python scripts/all-pdf-to-json-pdfplumber.py

process-smart:
	python scripts/all-pdf-to-json-smart.py

process-paddle:
	python scripts/all-pdf-to-json-paddle.py

process-tesseract:
	python scripts/all-pdf-to-json-tesseract.py

process-structured:
	python scripts/all-pdf-to-json-structured.py

process-smart-structured:
	python scripts/all-pdf-to-json-smart-structured.py

# Single file processing commands
# Usage: make process-single-fast FILE="path/to/document.pdf"
process-single-fast:
	python scripts/pdfplumber-to-json.py "$(FILE)"

process-single-paddle:
	python scripts/paddle-to-json.py "$(FILE)"

process-single-tesseract:
	python scripts/tesseract-to-json.py "$(FILE)"

all: install format lint test