#!/usr/bin/env python3
"""
Smart PDF to Structured JSON converter - Auto-detects OCR needs with enhanced output
Uses direct text extraction when possible, falls back to PaddleOCR for scanned pages
Produces structured JSON with metadata, document analysis, and intelligent processing
Optimized for Arabic legal documents
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

def extract_structured_text_from_pdf_smart(pdf_path):
    """Smart extraction with structured output: detect OCR needs per page and use appropriate method"""
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Enhanced structure with metadata and organized content
        pdf_data = {
            "metadata": {
                "filename": os.path.basename(pdf_path),
                "full_path": str(pdf_path),
                "file_size": os.path.getsize(pdf_path),
                "total_pages": total_pages,
                "extraction_date": datetime.now().isoformat(),
                "extraction_method": "Smart Hybrid (PyMuPDF + PaddleOCR)"
            },
            "document_info": {
                "title": doc.metadata.get('title', '').strip() or None,
                "author": doc.metadata.get('author', '').strip() or None,
                "subject": doc.metadata.get('subject', '').strip() or None,
                "creator": doc.metadata.get('creator', '').strip() or None,
                "producer": doc.metadata.get('producer', '').strip() or None,
                "creation_date": doc.metadata.get('creationDate', '').strip() or None,
                "modification_date": doc.metadata.get('modDate', '').strip() or None
            },
            "processing_info": {
                "smart_detection_used": True,
                "ocr_pages": 0,
                "direct_pages": 0,
                "failed_pages": 0,
                "processing_summary": ""
            },
            "content": {
                "full_text": "",
                "pages": [],
                "summary": {
                    "total_characters": 0,
                    "total_words": 0,
                    "non_empty_pages": 0,
                    "language_detected": "Arabic"
                }
            }
        }
        
        all_text_parts = []
        ocr = None
        ocr_pages = 0
        direct_pages = 0
        failed_pages = 0
        non_empty_pages = 0
        
        print(f"📄 Analyzing {total_pages} pages for extraction method...")
        
        # Process each page with smart detection
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # Detect if page needs OCR
            needs_ocr = detect_if_page_needs_ocr(page)
            extraction_method = "unknown"
            
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
                    extraction_method = "PaddleOCR"
                    ocr_pages += 1
                else:
                    print(f"   📖 Page {page_num + 1}: OCR failed, using direct")
                    page_text = extract_text_direct(page)
                    extraction_method = "PyMuPDF (OCR fallback)"
                    direct_pages += 1
            else:
                print(f"   📄 Page {page_num + 1}: Using direct extraction")
                page_text = extract_text_direct(page)
                extraction_method = "PyMuPDF"
                direct_pages += 1
            
            # Get raw text for reference (first 500 chars)
            try:
                raw_text = page.get_text("text", sort=True)
                raw_preview = raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
            except:
                raw_text = ""
                raw_preview = ""
            
            # Page-level information
            page_info = {
                "page_number": page_num + 1,
                "extraction_method": extraction_method,
                "needs_ocr_detected": needs_ocr,
                "raw_text_preview": raw_preview,
                "cleaned_text": page_text,
                "character_count": len(page_text),
                "word_count": len(page_text.split()) if page_text else 0,
                "has_content": bool(page_text.strip()),
                "processing_success": bool(page_text.strip())
            }
            
            pdf_data["content"]["pages"].append(page_info)
            
            if page_text.strip():
                all_text_parts.append(page_text)
                non_empty_pages += 1
            else:
                failed_pages += 1
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join(all_text_parts)
        pdf_data["content"]["full_text"] = full_text
        
        # Update processing info
        pdf_data["processing_info"]["ocr_pages"] = ocr_pages
        pdf_data["processing_info"]["direct_pages"] = direct_pages
        pdf_data["processing_info"]["failed_pages"] = failed_pages
        pdf_data["processing_info"]["processing_summary"] = f"{direct_pages} direct, {ocr_pages} OCR, {failed_pages} failed"
        
        # Update summary statistics
        pdf_data["content"]["summary"]["total_characters"] = len(full_text)
        pdf_data["content"]["summary"]["total_words"] = len(full_text.split()) if full_text else 0
        pdf_data["content"]["summary"]["non_empty_pages"] = non_empty_pages
        
        # Try to detect document type based on content patterns
        pdf_data["content"]["document_analysis"] = analyze_document_type(full_text)
        
        print(f"📊 Processing summary: {direct_pages} direct, {ocr_pages} OCR, {failed_pages} failed")
        return pdf_data
    
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
        return None

def analyze_document_type(text):
    """Analyze document content to determine type and extract key patterns"""
    analysis = {
        "document_type": "Unknown",
        "confidence": 0.0,
        "key_patterns": [],
        "legal_terms_found": [],
        "article_count": 0,
        "contains_dates": False
    }
    
    if not text:
        return analysis
    
    text_lower = text.lower()
    
    # Legal document patterns
    legal_patterns = {
        "regulation": ["نظام", "لائحة", "قانون", "تنظيم"],
        "court_ruling": ["حكم", "قرار", "محكمة", "قضية", "دعوى"],
        "contract": ["عقد", "اتفاقية", "مقاولة", "شراكة"],
        "law_article": ["مادة", "فقرة", "بند", "فصل"],
        "judicial_collection": ["مجموعة", "أحكام", "قضائية", "سابقة"]
    }
    
    # Count legal terms and determine document type
    max_count = 0
    detected_type = "Unknown"
    
    for doc_type, terms in legal_patterns.items():
        count = sum(text_lower.count(term) for term in terms)
        if count > max_count:
            max_count = count
            detected_type = doc_type
        
        # Add found terms to analysis
        found_terms = [term for term in terms if term in text_lower]
        if found_terms:
            analysis["legal_terms_found"].extend(found_terms)
    
    analysis["document_type"] = detected_type
    analysis["confidence"] = min(max_count / 10.0, 1.0)  # Normalize confidence
    
    # Count articles (مادة)
    article_matches = re.findall(r'مادة\s*(\d+)', text)
    analysis["article_count"] = len(article_matches)
    
    # Check for dates
    date_pattern = r'\d{4}/\d{1,2}/\d{1,2}|\d{4}هـ|\d{4}\s*م'
    analysis["contains_dates"] = bool(re.search(date_pattern, text))
    
    # Extract key patterns (first few words of significant sentences)
    sentences = text.split('.')[:5]  # First 5 sentences
    analysis["key_patterns"] = [s.strip()[:100] for s in sentences if len(s.strip()) > 10]
    
    return analysis

def clean_arabic_text(text):
    """Clean and normalize Arabic text with enhanced processing"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize spaces
    text = ' '.join(text.split())
    
    # Advanced Arabic normalization
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ي', 'ى')
    text = text.replace('ك', 'ك').replace('ي', 'ي')  # Normalize Yeh and Kaf
    
    # Remove diacritics but preserve structure
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670\u0640]')
    text = arabic_diacritics.sub('', text)
    
    # Clean up multiple spaces and normalize punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[۔؍؎؏؞؟]', '.', text)  # Normalize Arabic punctuation
    
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

def process_all_pdfs(data_dir="data", results_dir="hybrid_structured_results"):
    """Process all PDFs in data directory with smart extraction and structured output"""
    
    print(f"🚀 Starting smart structured batch PDF extraction")
    print(f"📂 Source: {data_dir}")
    print(f"📁 Output: {results_dir}")
    print("🧠 Auto-detecting OCR needs + Enhanced structured output")
    print("-" * 70)
    
    start_time = time.time()
    
    # Find all PDF files
    print("🔍 Scanning for PDF files...")
    pdf_files = find_all_pdfs(data_dir)
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print("-" * 70)
    
    # Create results directory
    results_path = Path(results_dir)
    results_path.mkdir(exist_ok=True)
    
    # Process each PDF file
    processed = 0
    failed = 0
    total_chars = 0
    total_ocr_pages = 0
    total_direct_pages = 0
    
    for i, (full_path, rel_path) in enumerate(pdf_files, 1):
        print(f"\n📖 Processing {i}/{len(pdf_files)}: {rel_path}")
        
        # Smart structured extraction
        result = extract_structured_text_from_pdf_smart(full_path)
        
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
        output_file = output_dir / f"{base_name}_smart_structured.json"
        
        # Save structured JSON
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            processed += 1
            char_count = result["content"]["summary"]["total_characters"]
            word_count = result["content"]["summary"]["total_words"]
            doc_type = result["content"]["document_analysis"]["document_type"]
            ocr_pages = result["processing_info"]["ocr_pages"]
            direct_pages = result["processing_info"]["direct_pages"]
            
            total_chars += char_count
            total_ocr_pages += ocr_pages
            total_direct_pages += direct_pages
            
            print(f"✅ Saved: {output_file}")
            print(f"   📊 {char_count:,} chars, {word_count:,} words, Type: {doc_type}")
            print(f"   🧠 Processing: {direct_pages} direct, {ocr_pages} OCR")
            
        except Exception as e:
            failed += 1
            print(f"❌ Error saving {rel_path}: {e}")
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("📊 SMART STRUCTURED BATCH PROCESSING SUMMARY")
    print("=" * 80)
    print(f"📄 Total files found: {len(pdf_files)}")
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total characters extracted: {total_chars:,}")
    print(f"🧠 Total pages processed: {total_direct_pages + total_ocr_pages}")
    print(f"   📄 Direct extraction: {total_direct_pages} pages")
    print(f"   📖 OCR processing: {total_ocr_pages} pages")
    print(f"⏱️  Total processing time: {total_time:.2f} seconds")
    print(f"📁 Structured results saved to: {results_dir}")
    print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if processed > 0:
        avg_time = total_time / processed
        avg_chars = total_chars / processed
        print(f"📈 Average time per file: {avg_time:.2f} seconds")
        print(f"📈 Average characters per file: {avg_chars:,.0f}")

def main():
    data_dir = "data"
    results_dir = "hybrid_structured_results"
    
    # Allow custom directories via command line
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        results_dir = sys.argv[2]
    
    print("🔧 Qaanoon AI - Smart Structured PDF to JSON Converter")
    print("Intelligent OCR detection + Enhanced metadata and document analysis")
    print()
    
    process_all_pdfs(data_dir, results_dir)

# Single file processing function for direct use
def process_single_file(pdf_path, output_dir="output"):
    """Process a single PDF file with smart structured extraction"""
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File '{pdf_path}' not found")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print("❌ Error: File must be a PDF")
        return
    
    print(f"🚀 Starting smart structured extraction: {pdf_path}")
    start_time = time.time()
    
    # Extract text with structured output
    result = extract_structured_text_from_pdf_smart(pdf_path)
    
    if result is None:
        print("❌ Failed to process PDF")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_smart_structured.json")
    
    # Save structured JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        char_count = result["content"]["summary"]["total_characters"]
        word_count = result["content"]["summary"]["total_words"]
        doc_type = result["content"]["document_analysis"]["document_type"]
        ocr_pages = result["processing_info"]["ocr_pages"]
        direct_pages = result["processing_info"]["direct_pages"]
        
        print(f"\n✅ Smart structured extraction complete!")
        print(f"📄 Text length: {char_count:,} characters, {word_count:,} words")
        print(f"🧠 Processing: {direct_pages} direct, {ocr_pages} OCR pages")
        print(f"📋 Document type: {doc_type}")
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
