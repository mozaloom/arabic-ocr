#!/usr/bin/env python3
"""
Simple PDF to JSON converter using PyMuPDF
Extracts clean text from PDF files and saves as simple JSON format
Optimized for Arabic legal documents
"""

import fitz  # PyMuPDF
import json
import os
import sys
import re
import time
from datetime import datetime

def extract_text_from_pdf(path):
    """Extract text from PDF and return simple JSON structure"""
    start_time = time.time()
    try:
        print("🔄 Opening PDF document...")
        doc = fitz.open(path)
        total_pages = len(doc)
        print(f"📄 Found {total_pages} pages")
        
        # Simple structure - just filename and clean text
        pdf_data = {
            "filename": os.path.basename(path),
            "text": ""
        }
        
        all_text_parts = []
        
        # Extract text from all pages with progress
        print("📖 Extracting text from pages...")
        for page_num in range(total_pages):
            if page_num % 5 == 0 or page_num == total_pages - 1:
                progress = ((page_num + 1) / total_pages) * 100
                print(f"   Processing page {page_num + 1}/{total_pages} ({progress:.1f}%)")
            
            page = doc.load_page(page_num)
            page_text = page.get_text("text", sort=True)
            cleaned_text = clean_arabic_text(page_text)
            
            if cleaned_text.strip():  # Only add non-empty pages
                all_text_parts.append(cleaned_text)
        
        doc.close()
        
        print("🔗 Combining text from all pages...")
        # Join all text with double newlines between pages
        pdf_data["text"] = "\n\n".join(all_text_parts)
        
        processing_time = time.time() - start_time
        print(f"⏱️  Text extraction completed in {processing_time:.2f} seconds")
        
        return pdf_data
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
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
    print(f"Debug: Number of arguments: {len(sys.argv)}")
    print(f"Debug: Arguments: {sys.argv}")
    
    if len(sys.argv) != 2:
        print("Usage: python pdfplumber-to-json.py <pdf_file>")
        print("Example: python pdfplumber-to-json.py document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        print("❌ Error: File must be a PDF")
        sys.exit(1)
    
    print(f"🚀 Starting extraction: {pdf_path}")
    start_time = time.time()
    
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
    output_file = os.path.join(output_dir, f"{base_name}_extracted.json")
    
    print("💾 Saving JSON file...")
    # Save JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        print(f"\n✅ Extraction complete!")
        print(f"📄 Text length: {len(result['text']):,} characters")
        print(f"⏱️  Total processing time: {total_time:.2f} seconds")
        print(f"💾 Saved to: {output_file}")
        print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
