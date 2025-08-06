#!/usr/bin/env python3
"""
Simple PDF to JSON converter using PaddleOCR
Extracts clean text from PDF files using OCR and saves as simple JSON format
Optimized for Arabic legal documents
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from paddleocr import PaddleOCR
import cv2
import fitz  # PyMuPDF for PDF handling
import numpy as np

def initialize_paddleocr():
    """Initialize PaddleOCR with Arabic and English support"""
    print("🔧 Initializing PaddleOCR with Arabic language support...")
    start_time = time.time()
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='arabic', show_log=False)
        init_time = time.time() - start_time
        print(f"✅ PaddleOCR initialized successfully in {init_time:.2f} seconds")
        return ocr
    except Exception as e:
        print(f"❌ Error initializing PaddleOCR: {str(e)}")
        return None

def extract_text_from_pdf(pdf_path, ocr):
    """Extract text from PDF using OCR and return simple JSON structure"""
    start_time = time.time()
    try:
        print("🔄 Opening PDF document...")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"📄 Found {total_pages} pages")
        
        # Simple structure - just filename and clean text
        pdf_data = {
            "filename": os.path.basename(pdf_path),
            "text": ""
        }
        
        all_text_parts = []
        
        print("🔍 Starting OCR processing...")
        # Process each page with progress tracking
        for page_num in range(total_pages):
            page_start = time.time()
            
            if page_num % 2 == 0 or page_num == total_pages - 1:
                progress = ((page_num + 1) / total_pages) * 100
                print(f"   📖 Processing page {page_num + 1}/{total_pages} ({progress:.1f}%)")
            
            page = doc.load_page(page_num)
            
            # Convert page to image for OCR
            print(f"      🖼️  Converting page {page_num + 1} to image...")
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to numpy array for PaddleOCR
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                print(f"      ⚠️  Warning: Could not process page {page_num + 1}")
                continue
            
            # Perform OCR
            print(f"      🔍 Running OCR on page {page_num + 1}...")
            ocr_result = ocr.ocr(img, cls=True)
            
            if not ocr_result or not ocr_result[0]:
                print(f"      ⚠️  No text detected on page {page_num + 1}")
                continue
            
            # Extract text from OCR results
            page_text = []
            for line in ocr_result[0]:
                if line and len(line) > 1:
                    text = line[1][0]  # Extract text from the result
                    if text.strip():
                        page_text.append(text.strip())
            
            if page_text:
                page_content = " ".join(page_text)
                cleaned_text = clean_arabic_text(page_content)
                if cleaned_text.strip():
                    all_text_parts.append(cleaned_text)
            
            page_time = time.time() - page_start
            print(f"      ⏱️  Page {page_num + 1} completed in {page_time:.2f}s")
        
        doc.close()
        
        print("🔗 Combining text from all pages...")
        # Join all text with double newlines between pages
        pdf_data["text"] = "\n\n".join(all_text_parts)
        
        processing_time = time.time() - start_time
        print(f"⏱️  OCR processing completed in {processing_time:.2f} seconds")
        
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
        print("Usage: python paddle-to-json.py <pdf_file>")
        print("Example: python paddle-to-json.py document.pdf")
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
    
    # Initialize OCR
    ocr = initialize_paddleocr()
    if ocr is None:
        sys.exit(1)
    
    # Extract text
    result = extract_text_from_pdf(pdf_path, ocr)
    
    if result is None:
        print("❌ Failed to process PDF")
        sys.exit(1)
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename in output directory
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_paddleocr.json")
    
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
