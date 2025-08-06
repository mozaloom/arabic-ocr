# PaddleOCR backend for text extraction
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import os
import numpy as np
from PIL import Image
from typing import List, Dict, Any
import json

class PaddleOCRBackend:
    """PaddleOCR backend for text extraction from images and PDFs."""
    
    def __init__(self, use_textline_orientation=True, lang='en', use_gpu=True):
        """
        Initialize PaddleOCR instance.
        
        Args:
            use_textline_orientation: Whether to use text line orientation
            lang: Language for OCR ('en', 'ch', 'ar', etc.)
            use_gpu: Whether to use GPU acceleration
        """
        try:
            self.ocr = PaddleOCR(
                use_textline_orientation=use_textline_orientation,
                lang=lang,
                device='gpu' if use_gpu else 'cpu'
            )
            print(f"PaddleOCR initialized with device: {'GPU' if use_gpu else 'CPU'}")
        except Exception as e:
            print(f"Failed to initialize with GPU, falling back to CPU: {e}")
            self.ocr = PaddleOCR(
                use_textline_orientation=use_textline_orientation,
                lang=lang,
                device='cpu'
            )
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Run OCR on the image - PaddleOCR.ocr() is the correct method
            result = self.ocr.ocr(image_path)
            
            # Extract text and confidence scores
            extracted_text = []
            total_confidence = 0
            word_count = 0
            
            # PaddleOCR returns a list of pages, each page is a list of line results
            if result and len(result) > 0:
                page_result = result[0]  # Get first page
                
                if page_result:  # Check if page has content
                    for line_result in page_result:
                        if line_result and len(line_result) >= 2:
                            # line_result format: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
                            text_info = line_result[1]
                            if text_info and len(text_info) >= 2:
                                text = text_info[0]
                                confidence = text_info[1]
                                
                                if text and text.strip():
                                    extracted_text.append(text)
                                    total_confidence += confidence
                                    word_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / word_count if word_count > 0 else 0
            
            return {
                'text': '\n'.join(extracted_text),
                'word_count': word_count,
                'avg_confidence': avg_confidence,
                'raw_result': result
            }
            
        except Exception as e:
            return {
                'text': '',
                'word_count': 0,
                'avg_confidence': 0,
                'error': str(e),
                'raw_result': None
            }
    
    def extract_text_from_pdf(self, pdf_path: str, pages: List[int] = None, dpi: int = 300) -> Dict[str, Any]:
        """
        Extract text from PDF by converting to images first.
        
        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (0-indexed). If None, process all pages
            dpi: DPI for PDF to image conversion
            
        Returns:
            Dictionary containing extracted text and metadata for all pages
        """
        try:
            # Convert PDF to images
            if pages:
                # Convert only specified pages one by one to avoid range issues
                images = []
                actual_page_numbers = []
                for page_num in pages:
                    # pdf2image uses 1-based indexing, pages parameter is 0-based
                    page_images = convert_from_path(
                        pdf_path, 
                        dpi=dpi,
                        first_page=page_num + 1,
                        last_page=page_num + 1
                    )
                    if page_images:
                        images.extend(page_images)
                        actual_page_numbers.append(page_num)
            else:
                # Convert all pages
                images = convert_from_path(pdf_path, dpi=dpi)
                actual_page_numbers = list(range(len(images)))
            
            all_results = []
            total_text = []
            total_confidence = 0
            total_words = 0
            
            for i, image in enumerate(images):
                # Get the actual page number
                actual_page_num = actual_page_numbers[i]
                
                print(f"Processing page {actual_page_num + 1}")
                
                # Save image temporarily
                temp_image_path = f"temp_page_{actual_page_num}.jpg"
                image.save(temp_image_path, 'JPEG')
                
                # Extract text from this page
                page_result = self.extract_text_from_image(temp_image_path)
                page_result['page_number'] = actual_page_num + 1  # 1-indexed for display
                all_results.append(page_result)
                
                # Accumulate statistics
                if page_result['text']:
                    total_text.append(f"--- Page {actual_page_num + 1} ---")
                    total_text.append(page_result['text'])
                    total_confidence += page_result['avg_confidence'] * page_result['word_count']
                    total_words += page_result['word_count']
                
                # Clean up temporary file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                
                # Print progress
                if page_result.get('error'):
                    print(f"  Error on page {actual_page_num + 1}: {page_result['error']}")
                else:
                    print(f"  Extracted {page_result['word_count']} words from page {actual_page_num + 1}")
            
            # Calculate overall statistics
            overall_confidence = total_confidence / total_words if total_words > 0 else 0
            
            return {
                'full_text': '\n'.join(total_text),
                'total_pages': len(images),
                'total_words': total_words,
                'overall_confidence': overall_confidence,
                'page_results': all_results
            }
            
        except Exception as e:
            return {
                'full_text': '',
                'total_pages': 0,
                'total_words': 0,
                'overall_confidence': 0,
                'error': str(e),
                'page_results': []
            }

def main():
    """Test the PaddleOCR backend."""
    # Initialize the backend with GPU support
    paddle_ocr = PaddleOCRBackend(lang='en', use_gpu=True)  # Enable GPU
    
    # Test with PDF
    pdf_path = "pdfs/النظام الجزائي لجرائم التزوير.pdf"
    
    if os.path.exists(pdf_path):
        print(f"Processing PDF: {pdf_path}")
        result = paddle_ocr.extract_text_from_pdf(pdf_path)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully processed {result['total_pages']} pages")
            print(f"Total words: {result['total_words']}")
            print(f"Overall confidence: {result['overall_confidence']:.2f}")
            print("\nExtracted text (first 500 characters):")
            print(result['full_text'][:500] + "..." if len(result['full_text']) > 500 else result['full_text'])
            
            # Save results to file
            os.makedirs("output", exist_ok=True)
            with open("output/paddleocr_results.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\nResults saved to output/paddleocr_results.json")
    else:
        print(f"PDF file not found: {pdf_path}")

if __name__ == "__main__":
    main()
