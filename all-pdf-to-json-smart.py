#!/usr/bin/env python3
"""
Smart PDF to JSON converter - Auto-detects OCR needs
Uses direct text extraction when possible, falls back to PaddleOCR for scanned pages
Optimized for Arabic legal documents with intelligent processing
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF for PDF handling
from paddleocr import PaddleOCR
import cv2
import numpy as np

def initialize_paddleocr():
    """Initialize PaddleOCR with Arabic and English support (lazy loading)"""
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='arabic', show_log=False)
        return ocr
    except Exception as e:
        print(f"❌ Error initializing PaddleOCR: {str(e)}")
        return None

def detect_if_page_needs_ocr(page, threshold_chars=50, threshold_ratio=0.3):
    """
    Detect if a page needs OCR by analyzing extracted text quality
    
    Args:
        page: PyMuPDF page object
        threshold_chars: Minimum characters needed to consider page has text
        threshold_ratio: Minimum ratio of valid text characters
    
    Returns:
        bool: True if page needs OCR, False if direct text extraction is sufficient
    """
    try:
        # Try direct text extraction
        direct_text = page.get_text("text", sort=True)
        
        # If no text found, definitely needs OCR
        if not direct_text or len(direct_text.strip()) < threshold_chars:
            return True
        
        # Count valid characters vs total characters
        total_chars = len(direct_text.strip())
        
        # Count Arabic, English, numbers, and common punctuation as valid
        valid_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077Fa-zA-Z0-9\s\.\,\:\;\!\?\(\)\-\+\=]', direct_text))
        
        # Calculate ratio of valid characters
        if total_chars == 0:
            return True
        
        valid_ratio = valid_chars / total_chars
        
        # If too many invalid/garbled characters, use OCR
        if valid_ratio < threshold_ratio:
            return True
        
        # Additional checks for common OCR artifacts
        ocr_artifacts = ['�', '□', '▪', '◦', '●']
        artifact_count = sum(direct_text.count(artifact) for artifact in ocr_artifacts)
        
        # If more than 5% artifacts, use OCR
        if total_chars > 0 and (artifact_count / total_chars) > 0.05:
            return True
        
        return False
        
    except Exception:
        # If any error in detection, default to OCR
        return True

def extract_text_direct(page):
    """Extract text directly from PDF page"""
    try:
        text = page.get_text("text", sort=True)
        return clean_arabic_text(text)
    except Exception:
        return ""

def extract_text_ocr(page, ocr):
    """Extract text using OCR from PDF page"""
    try:
        # Convert page to image for OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        img_data = pix.tobytes("png")
        
        # Convert to numpy array for PaddleOCR
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return ""
        
        # Perform OCR
        ocr_result = ocr.ocr(img, cls=True)
        
        if not ocr_result or not ocr_result[0]:
            return ""
        
        # Extract text from OCR results
        page_text = []
        for line in ocr_result[0]:
            if line and len(line) > 1:
                text = line[1][0]  # Extract text from the result
                if text.strip():
                    page_text.append(text.strip())
        
        if page_text:
            page_content = " ".join(page_text)
            return clean_arabic_text(page_content)
        
        return ""
        
    except Exception as e:
        return ""

def extract_text_from_pdf_smart(pdf_path):
    """Smart extraction: detect OCR needs per page and use appropriate method"""
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Simple structure - just filename and clean text
        pdf_data = {
            "filename": os.path.basename(pdf_path),
            "text": ""
        }
        
        all_text_parts = []
        ocr = None
        ocr_pages = 0
        direct_pages = 0
        
        print(f"📄 Analyzing {total_pages} pages for extraction method...")
        
        # Process each page with smart detection
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # Detect if page needs OCR
            needs_ocr = detect_if_page_needs_ocr(page)
            
            if needs_ocr:
                # Initialize OCR if not done yet
                if ocr is None:
                    print("🔧 Initializing PaddleOCR for scanned pages...")
                    ocr = initialize_paddleocr()
                    if ocr is None:
                        print("❌ PaddleOCR initialization failed, using direct extraction")
                        needs_ocr = False
                
                if ocr is not None:
                    print(f"   📖 Page {page_num + 1}: Using OCR")
                    page_text = extract_text_ocr(page, ocr)
                    ocr_pages += 1
                else:
                    print(f"   📖 Page {page_num + 1}: OCR failed, using direct")
                    page_text = extract_text_direct(page)
                    direct_pages += 1
            else:
                print(f"   📄 Page {page_num + 1}: Using direct extraction")
                page_text = extract_text_direct(page)
                direct_pages += 1
            
            if page_text.strip():
                all_text_parts.append(page_text)
        
        doc.close()
        
        # Join all text with double newlines between pages
        pdf_data["text"] = "\n\n".join(all_text_parts)
        
        print(f"📊 Processing summary: {direct_pages} direct, {ocr_pages} OCR")
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

def process_all_pdfs(data_dir="data", results_dir="hybrid_results"):
    """Process all PDFs in data directory with smart extraction method selection"""
    
    print(f"🚀 Starting smart batch PDF extraction")
    print(f"📂 Source: {data_dir}")
    print(f"📁 Output: {results_dir}")
    print("🧠 Auto-detecting OCR needs per page")
    print("-" * 60)
    
    start_time = time.time()
    
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
    total_direct_pages = 0
    total_ocr_pages = 0
    
    for i, (full_path, rel_path) in enumerate(pdf_files, 1):
        print(f"\n📖 Processing {i}/{len(pdf_files)}: {rel_path}")
        
        # Smart extraction
        result = extract_text_from_pdf_smart(full_path)
        
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
        output_file = output_dir / f"{base_name}_smart.json"
        
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
    print("📊 SMART BATCH PROCESSING SUMMARY")
    print("=" * 70)
    print(f"📄 Total files found: {len(pdf_files)}")
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total processing time: {total_time:.2f} seconds")
    print(f"📁 Results saved to: {results_dir}")
    print(f"🧠 Method: Smart detection (Direct + OCR as needed)")
    print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if processed > 0:
        avg_time = total_time / processed
        print(f"📈 Average time per file: {avg_time:.2f} seconds")

def main():
    data_dir = "data"
    results_dir = "hybrid_results"
    
    # Allow custom directories via command line
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        results_dir = sys.argv[2]
    
    print("🔧 Qaanoon AI - Smart PDF to JSON Converter")
    print("Intelligent OCR detection: Direct extraction + PaddleOCR fallback")
    print()
    
    process_all_pdfs(data_dir, results_dir)

# Single file processing function for direct use
def process_single_file(pdf_path, output_dir="output"):
    """Process a single PDF file with smart extraction"""
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print("❌ Error: File must be a PDF")
        return
    
    print(f"🚀 Starting smart extraction: {pdf_path}")
    start_time = time.time()
    
    # Extract text
    result = extract_text_from_pdf_smart(pdf_path)
    
    if result is None:
        print("❌ Failed to process PDF")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_smart.json")
    
    # Save JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        print(f"\n✅ Smart extraction complete!")
        print(f"📄 Text length: {len(result['text']):,} characters")
        print(f"⏱️  Total processing time: {total_time:.2f} seconds")
        print(f"💾 Saved to: {output_file}")
        print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    # Check if single file mode (file path provided)
    if len(sys.argv) == 2 and sys.argv[1].endswith('.pdf'):
        process_single_file(sys.argv[1])
    else:
        main()
