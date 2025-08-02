# Simple PaddleOCR backend using traditional API
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import os
import json
from PIL import Image
from typing import List, Dict, Any

class PaddleOCRBackend:
    """PaddleOCR backend for text extraction from images and PDFs."""
    
    def __init__(self, use_angle_cls=True, lang='en'):
        """
        Initialize PaddleOCR instance with simple parameters.
        
        Args:
            use_angle_cls: Whether to use angle classification
            lang: Language for OCR ('en', 'ch', 'ar', etc.)
        """
        try:
            # Use the simple, traditional PaddleOCR initialization
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang
            )
            print(f"PaddleOCR initialized successfully with language: {lang}")
        except Exception as e:
            print(f"Failed to initialize PaddleOCR: {e}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from a single image using traditional OCR method.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Use the traditional ocr() method
            result = self.ocr.ocr(image_path, cls=True)
            
            # Extract text and confidence scores
            extracted_text = []
            total_confidence = 0
            word_count = 0
            
            # Parse the traditional OCR result format
            if result and result[0]:
                for line in result[0]:
                    if line:
                        text = line[1][0]  # Text content
                        confidence = line[1][1]  # Confidence score
                        
                        if text and text.strip():
                            extracted_text.append(text.strip())
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
    
    def extract_text_from_pdf(self, pdf_path: str, dpi: int = 150) -> Dict[str, Any]:
        """
        Extract text from PDF by converting to images first.
        Using lower DPI to reduce memory usage.
        """
        try:
            # Convert PDF to images with lower DPI to save memory
            print(f"Converting PDF to images with DPI: {dpi}")
            images = convert_from_path(pdf_path, dpi=dpi)
            
            all_results = []
            total_text = []
            total_confidence = 0
            total_words = 0
            
            for i, image in enumerate(images):
                print(f"Processing page {i + 1}/{len(images)}")
                
                # Save image temporarily
                temp_image_path = f"temp_page_{i}.jpg"
                image.save(temp_image_path, 'JPEG', quality=85)
                
                # Extract text from this page
                page_result = self.extract_text_from_image(temp_image_path)
                page_result['page_number'] = i + 1
                all_results.append(page_result)
                
                # Accumulate statistics
                if page_result['text']:
                    total_text.append(f"--- Page {i + 1} ---")
                    total_text.append(page_result['text'])
                    total_confidence += page_result['avg_confidence'] * page_result['word_count']
                    total_words += page_result['word_count']
                
                # Clean up temporary file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                
                # Print progress
                if page_result.get('error'):
                    print(f"  Error on page {i + 1}: {page_result['error']}")
                else:
                    print(f"  Extracted {page_result['word_count']} words from page {i + 1}")
            
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
    try:
        # Initialize the backend with simple parameters
        paddle_ocr = PaddleOCRBackend(lang='ar')
        
        # Test with PDF
        pdf_path = "pdfs/النظام الجزائي لجرائم التزوير.pdf"
        
        if os.path.exists(pdf_path):
            print(f"Processing PDF: {pdf_path}")
            result = paddle_ocr.extract_text_from_pdf(pdf_path, dpi=120)  # Even lower DPI
            
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
                    # Remove raw_result from page_results to avoid JSON serialization issues
                    clean_result = result.copy()
                    for page in clean_result['page_results']:
                        if 'raw_result' in page:
                            page['raw_result'] = str(page['raw_result'])[:200] + "..." if page['raw_result'] else None
                    
                    json.dump(clean_result, f, ensure_ascii=False, indent=2)
                print("\nResults saved to output/paddleocr_results.json")
        else:
            print(f"PDF file not found: {pdf_path}")
            
    except Exception as e:
        print(f"Failed to initialize or run PaddleOCR: {e}")

if __name__ == "__main__":
    main()
