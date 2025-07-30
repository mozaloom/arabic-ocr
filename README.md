# qaanoon-ai

the text extraction structure tree structure:
```
src/
├── ocr/                        # All OCR models
│   ├── __init__.py
│   ├── easyocr_backend.py
│   ├── paddleocr_backend.py
│   ├── tesseract_backend.py
│   └── trocr_backend.py
│
├── extraction/                # Text extraction logic
│   ├── __init__.py
│   ├── pdf_text_extractor.py  # For text-based PDFs
│   └── image_text_extractor.py  # For scanned PDFs
│
├── utils/                     # Utility scripts
│   ├── file_handler.py        # File I/O, format detection
│   └── logger.py              # Logging functions
│
├── main.py                    # Entry point (CLI, GUI, or script)
└── config.py                  # Configs / model options / thresholds
``` 

