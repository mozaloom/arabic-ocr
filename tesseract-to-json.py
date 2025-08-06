#!/usr/bin/env python3
"""
Simple PDF to JSON converter using Tesseract OCR
Extracts clean text from PDF files using OCR and saves as simple JSON format
Optimized for Arabic legal documents
"""

import os
import sys
import json
import re
import time
from datetime import datetime
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for PDF handling
import cv2
import numpy as np

def initialize_tesseract():
    """Initialize Tesseract with Arabic and English support"""
    print("🔧 Initializing Tesseract OCR...")
    init_start = time.time()
    
    try:
        version = pytesseract.get_tesseract_version()
        init_time = time.time() - init_start
        print(f"✅ Tesseract initialized successfully (Version: {version}) - {init_time:.2f}s")
        return True
    except Exception as e:
        print(f"❌ Error initializing Tesseract: {str(e)}")
        return False

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using OCR and return simple JSON structure"""
    try:
        print("📖 Opening PDF document...")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"📄 Document has {total_pages} page(s)")
        
        # Simple structure - just filename and clean text
        pdf_data = {
            "filename": os.path.basename(pdf_path),
            "text": ""
        }
        
        all_text_parts = []
        
        # Configure Tesseract for Arabic and English
        custom_config = r'--oem 3 --psm 6 -l ara+eng'
        
        print("🔄 Starting OCR processing...")
        
        # Process each page
        for page_num in range(total_pages):
            page_start = time.time()
            page = doc.load_page(page_num)
            
            print(f"  📄 Processing page {page_num + 1}/{total_pages}...", end="")
            
            # Convert page to image for OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image for Tesseract
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                print(" ⚠️  Skipped (image conversion failed)")
                continue
            
            # Convert BGR to RGB for PIL
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
            # Perform OCR
            try:
                page_text = pytesseract.image_to_string(pil_image, config=custom_config)
                if page_text.strip():
                    cleaned_text = clean_arabic_text(page_text)
                    if cleaned_text.strip():
                        all_text_parts.append(cleaned_text)
                        
                page_time = time.time() - page_start
                print(f" ✅ ({page_time:.2f}s)")
                
            except Exception as e:
                page_time = time.time() - page_start
                print(f" ❌ OCR failed ({page_time:.2f}s): {e}")
                continue
        
        doc.close()
        
        # Join all text with double newlines between pages
        pdf_data["text"] = "\n\n".join(all_text_parts)
        
        return pdf_data
    
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return None

def clean_arabic_text(text):
    """Clean and normalize Arabic text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Basic Arabic normalization
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ي', 'ى')
    
    # Remove diacritics (optional)
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670\u0640]')
    text = arabic_diacritics.sub('', text)
    
    return text.strip()

def main():
    if len(sys.argv) != 2:
        print("Usage: python tesseract-to-json.py <pdf_file>")
        print("Example: python tesseract-to-json.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        print("❌ Error: File must be a PDF")
        sys.exit(1)
    
    print(f"🚀 Starting OCR extraction: {pdf_path}")
    start_time = time.time()
    
    # Initialize Tesseract
    if not initialize_tesseract():
        sys.exit(1)
    
    # Extract text
    result = extract_text_from_pdf(pdf_path)
    
    if result is None:
        print("❌ Failed to process PDF")
        sys.exit(1)
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename in output directory
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_tesseract.json")
    
    print("💾 Saving JSON file...")
    # Save JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        print(f"\n✅ OCR extraction complete!")
        print(f"📄 Text length: {len(result['text']):,} characters")
        print(f"⏱️  Total processing time: {total_time:.2f} seconds")
        print(f"💾 Saved to: {output_file}")
        print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
