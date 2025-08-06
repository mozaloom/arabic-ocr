#!/usr/bin/env python3
"""
Batch PDF to Structured JSON converter using PyMuPDF
Processes all PDF files in the data directory and creates structured, readable JSON output
Optimized for Arabic legal documents with enhanced metadata and organization
"""

import fitz  # PyMuPDF
import json
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path

def extract_structured_text_from_pdf(path):
    """Extract text from PDF and return structured JSON with enhanced metadata"""
    try:
        doc = fitz.open(path)
        total_pages = len(doc)
        
        # Enhanced structure with metadata and organized content
        pdf_data = {
            "metadata": {
                "filename": os.path.basename(path),
                "full_path": str(path),
                "file_size": os.path.getsize(path),
                "total_pages": total_pages,
                "extraction_date": datetime.now().isoformat(),
                "extraction_method": "PyMuPDF"
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
        non_empty_pages = 0
        
        # Extract text from each page with detailed information
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            page_text = page.get_text("text", sort=True)
            cleaned_text = clean_arabic_text(page_text)
            
            # Page-level information
            page_info = {
                "page_number": page_num + 1,
                "raw_text": page_text[:500] + "..." if len(page_text) > 500 else page_text,  # First 500 chars for reference
                "cleaned_text": cleaned_text,
                "character_count": len(cleaned_text),
                "word_count": len(cleaned_text.split()) if cleaned_text else 0,
                "has_content": bool(cleaned_text.strip())
            }
            
            pdf_data["content"]["pages"].append(page_info)
            
            if cleaned_text.strip():  # Only add non-empty pages to full text
                all_text_parts.append(cleaned_text)
                non_empty_pages += 1
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join(all_text_parts)
        pdf_data["content"]["full_text"] = full_text
        
        # Update summary statistics
        pdf_data["content"]["summary"]["total_characters"] = len(full_text)
        pdf_data["content"]["summary"]["total_words"] = len(full_text.split()) if full_text else 0
        pdf_data["content"]["summary"]["non_empty_pages"] = non_empty_pages
        
        # Try to detect document type based on content patterns
        pdf_data["content"]["document_analysis"] = analyze_document_type(full_text)
        
        return pdf_data
    
    except Exception as e:
        print(f"❌ Error processing {path}: {str(e)}")
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

def process_all_pdfs(data_dir="data", results_dir="structured_results"):
    """Process all PDFs in data directory and save structured JSON to results directory"""
    
    print(f"🚀 Starting structured PDF extraction")
    print(f"📂 Source: {data_dir}")
    print(f"📁 Output: {results_dir}")
    print("📋 Format: Enhanced structured JSON with metadata")
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
    total_chars = 0
    
    for i, (full_path, rel_path) in enumerate(pdf_files, 1):
        print(f"\n📖 Processing {i}/{len(pdf_files)}: {rel_path}")
        
        # Extract structured text
        result = extract_structured_text_from_pdf(full_path)
        
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
        output_file = output_dir / f"{base_name}_structured.json"
        
        # Save structured JSON
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            processed += 1
            char_count = result["content"]["summary"]["total_characters"]
            word_count = result["content"]["summary"]["total_words"]
            doc_type = result["content"]["document_analysis"]["document_type"]
            total_chars += char_count
            
            print(f"✅ Saved: {output_file}")
            print(f"   📊 {char_count:,} chars, {word_count:,} words, Type: {doc_type}")
            
        except Exception as e:
            failed += 1
            print(f"❌ Error saving {rel_path}: {e}")
    
    # Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("📊 STRUCTURED BATCH PROCESSING SUMMARY")
    print("=" * 70)
    print(f"📄 Total files found: {len(pdf_files)}")
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"📝 Total characters extracted: {total_chars:,}")
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
    results_dir = "structured_results"
    
    # Allow custom directories via command line
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        results_dir = sys.argv[2]
    
    print("🔧 Qaanoon AI - Structured PDF to JSON Converter")
    print("Enhanced with metadata, document analysis, and organized content")
    print()
    
    process_all_pdfs(data_dir, results_dir)

if __name__ == "__main__":
    main()
