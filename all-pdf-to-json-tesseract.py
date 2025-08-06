#!/usr/bin/env python3
"""
Batch PDF to JSON converter using Tesseract OCR
Processes all PDF files in the data directory and preserves directory structure in results
Optimized for Arabic legal documents using OCR
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
import pytesseract
from PIL import Image
import fitz  # PyMuPDF for PDF handling
import cv2
import numpy as np

def initialize_tesseract():
    """Initialize Tesseract with Arabic and English support"""
    try:
        version = pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        print(f"❌ Error initializing Tesseract: {str(e)}")
        return False

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using OCR and return simple JSON structure"""
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Simple structure - just filename and clean text
        pdf_data = {
            "filename": os.path.basename(pdf_path),
            "text": ""
        }
        
        all_text_parts = []
        
        # Configure Tesseract for Arabic and English
        custom_config = r'--oem 3 --psm 6 -l ara+eng'
        
        # Process each page
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # Convert page to image for OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image for Tesseract
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
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
            except Exception as e:
                continue
        
        doc.close()
        
        # Join all text with double newlines between pages
        pdf_data["text"] = "\n\n".join(all_text_parts)
        
        return pdf_data
    
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
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

def find_all_pdfs(data_dir):
    """Find all PDF files in the data directory and return with their relative paths"""
    pdf_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ Error: Data directory '{data_dir}' not found")
        return []
    
    # Walk through all subdirectories
    for pdf_file in data_path.rglob("*.pdf"):
        # Get relative path from data directory
        rel_path = pdf_file.relative_to(data_path)
        pdf_files.append((str(pdf_file), str(rel_path)))
    
    return pdf_files

def process_all_pdfs(data_dir="data", results_dir="results"):
    """Process all PDFs in data directory and save to results directory with same structure"""
    
    print(f"🚀 Starting batch PDF OCR extraction with Tesseract")
    print(f"📂 Source: {data_dir}")
    print(f"📁 Output: {results_dir}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Initialize Tesseract
    print("🔧 Initializing Tesseract OCR...")
    init_start = time.time()
    if not initialize_tesseract():
        print("❌ Failed to initialize Tesseract")
        return
    
    init_time = time.time() - init_start
    print(f"✅ Tesseract initialized in {init_time:.2f} seconds")
    
    # Find all PDF files
    print("🔍 Scanning for PDF files...")
    pdf_files = find_all_pdfs(data_dir)
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print("-" * 60)
    
    # Create results directory
    results_path = Path(results_dir)
    results_path.mkdir(exist_ok=True)
    
    # Process each PDF file
    processed = 0
    failed = 0
    
    for i, (full_path, rel_path) in enumerate(pdf_files, 1):
        print(f"\n📖 Processing {i}/{len(pdf_files)}: {rel_path}")
        
        # Extract text using OCR
        result = extract_text_from_pdf(full_path)
        
        if result is None:
            failed += 1
            print(f"❌ Failed to process: {rel_path}")
            continue
        
        # Create output path with same directory structure
        rel_path_obj = Path(rel_path)
        output_dir = results_path / rel_path_obj.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        base_name = rel_path_obj.stem
        output_file = output_dir / f"{base_name}_tesseract.json"
        
        # Save JSON
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            processed += 1
            char_count = len(result['text'])
            print(f"✅ Saved: {output_file} ({char_count:,} characters)")
            
        except Exception as e:
            failed += 1
            print(f"❌ Error saving {rel_path}: {e}")
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("📊 BATCH OCR PROCESSING SUMMARY (Tesseract)")
    print("=" * 70)
    print(f"📄 Total files found: {len(pdf_files)}")
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total processing time: {total_time:.2f} seconds")
    print(f"📁 Results saved to: {results_dir}")
    print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if processed > 0:
        avg_time = total_time / processed
        print(f"📈 Average time per file: {avg_time:.2f} seconds")

def main():
    data_dir = "data"
    results_dir = "results"
    
    # Allow custom directories via command line
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        results_dir = sys.argv[2]
    
    print("🔧 Qaanoon AI - Batch PDF to JSON Converter (Tesseract)")
    print("Using Tesseract OCR for Arabic text extraction")
    print()
    
    process_all_pdfs(data_dir, results_dir)

if __name__ == "__main__":
    main()
