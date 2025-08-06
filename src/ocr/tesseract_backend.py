"""
Tesseract OCR backend for text extraction from PDFs
Supports Arabic and English text recognition with pytesseract
"""

import pytesseract
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import logging
import time
import os
import subprocess
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TesseractBackend:
    """Tesseract OCR implementation for PDF text extraction"""
    
    def __init__(self, languages='ara+eng', tesseract_cmd=None):
        """
        Initialize Tesseract backend
        
        Args:
            languages: Language codes for Tesseract (e.g., 'ara+eng' for Arabic and English)
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self.languages = languages
        
        # Set tesseract command path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self._check_tesseract_installation()
        self._check_language_support()
    
    def _check_tesseract_installation(self):
        """Check if Tesseract is properly installed"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found or not properly configured: {e}")
            raise RuntimeError("Tesseract OCR not available. Please install tesseract-ocr.")
    
    def _check_language_support(self):
        """Check if required languages are supported"""
        try:
            available_languages = pytesseract.get_languages()
            required_langs = self.languages.replace('+', ' ').split()
            
            missing_langs = []
            for lang in required_langs:
                if lang not in available_languages:
                    missing_langs.append(lang)
            
            if missing_langs:
                logger.warning(f"Missing language data for: {missing_langs}")
                logger.info(f"Available languages: {available_languages}")
            else:
                logger.info(f"All required languages available: {required_langs}")
                
        except Exception as e:
            logger.warning(f"Could not check language support: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str, pages: List[int] = None, 
                             dpi: int = 200, psm: int = 6) -> Dict[str, Any]:
        """
        Extract text from PDF using Tesseract
        
        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (0-indexed). If None, process all pages
            dpi: DPI for PDF to image conversion
            psm: Page Segmentation Mode for Tesseract (6 = uniform block of text)
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        start_time = time.time()
        results = {
            'full_text': '',
            'page_results': [],
            'total_pages': 0,
            'total_words': 0,
            'overall_confidence': 0.0,
            'processing_time': 0.0,
            'backend': 'Tesseract'
        }
        
        try:
            # Configure Tesseract
            config = f'--psm {psm} -l {self.languages}'
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path}")
            pdf_images = convert_from_path(
                pdf_path, 
                dpi=dpi,
                first_page=pages[0] + 1 if pages else None,
                last_page=pages[-1] + 1 if pages else None
            )
            
            results['total_pages'] = len(pdf_images)
            logger.info(f"Converted {len(pdf_images)} pages to images")
            
            all_confidences = []
            page_texts = []
            
            for page_num, image in enumerate(pdf_images):
                actual_page_num = pages[page_num] if pages else page_num
                logger.info(f"Processing page {actual_page_num + 1}")
                
                # Extract text using Tesseract
                try:
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang=self.languages,
                        config=f'--psm {psm}'
                    )
                    
                    # Get detailed data with confidence scores
                    detailed_data = pytesseract.image_to_data(
                        image,
                        lang=self.languages,
                        config=f'--psm {psm}',
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Extract confidence scores
                    confidences = []
                    raw_results = []
                    
                    for i, confidence in enumerate(detailed_data['conf']):
                        if int(confidence) > 0:  # Valid confidence score
                            word = detailed_data['text'][i].strip()
                            if word:  # Non-empty word
                                confidences.append(int(confidence))
                                raw_results.append({
                                    'bbox': [
                                        detailed_data['left'][i],
                                        detailed_data['top'][i],
                                        detailed_data['left'][i] + detailed_data['width'][i],
                                        detailed_data['top'][i] + detailed_data['height'][i]
                                    ],
                                    'text': word,
                                    'confidence': int(confidence) / 100.0  # Convert to 0-1 scale
                                })
                    
                    page_word_count = len(page_text.split()) if page_text.strip() else 0
                    page_avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
                    
                    # Store page results
                    page_result = {
                        'page_number': actual_page_num + 1,
                        'text': page_text.strip(),
                        'word_count': page_word_count,
                        'avg_confidence': float(page_avg_confidence),
                        'raw_result': raw_results
                    }
                    
                    results['page_results'].append(page_result)
                    page_texts.append(f"--- Page {actual_page_num + 1} ---\n{page_text.strip()}")
                    
                    if confidences:
                        all_confidences.extend([c / 100.0 for c in confidences])
                    
                    logger.info(f"Page {actual_page_num + 1}: {page_word_count} words, "
                               f"avg confidence: {page_avg_confidence:.3f}")
                    
                except Exception as e:
                    logger.error(f"Error processing page {actual_page_num + 1}: {e}")
                    # Add empty page result
                    page_result = {
                        'page_number': actual_page_num + 1,
                        'text': '',
                        'word_count': 0,
                        'avg_confidence': 0.0,
                        'raw_result': [],
                        'error': str(e)
                    }
                    results['page_results'].append(page_result)
                    page_texts.append(f"--- Page {actual_page_num + 1} ---\n[Error: {e}]")
            
            # Combine results
            results['full_text'] = '\n'.join(page_texts)
            results['total_words'] = sum(page['word_count'] for page in results['page_results'])
            results['overall_confidence'] = float(np.mean(all_confidences)) if all_confidences else 0.0
            results['processing_time'] = time.time() - start_time
            
            logger.info(f"Tesseract extraction completed: {results['total_words']} words, "
                       f"overall confidence: {results['overall_confidence']:.3f}, "
                       f"time: {results['processing_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during Tesseract text extraction: {e}")
            raise
    
    def benchmark_performance(self, pdf_path: str, num_pages: int = 3) -> Dict[str, float]:
        """
        Benchmark the performance of Tesseract on the given PDF
        
        Args:
            pdf_path: Path to the PDF file
            num_pages: Number of pages to benchmark
            
        Returns:
            Dictionary containing performance metrics
        """
        try:
            results = self.extract_text_from_pdf(pdf_path, pages=list(range(num_pages)))
            
            return {
                'processing_time': results['processing_time'],
                'pages_per_second': results['total_pages'] / results['processing_time'],
                'words_per_second': results['total_words'] / results['processing_time'],
                'average_confidence': results['overall_confidence'],
                'total_words': results['total_words'],
                'backend': 'Tesseract'
            }
        except Exception as e:
            logger.error(f"Error during Tesseract benchmarking: {e}")
            return {
                'processing_time': float('inf'),
                'pages_per_second': 0,
                'words_per_second': 0,
                'average_confidence': 0,
                'total_words': 0,
                'backend': 'Tesseract',
                'error': str(e)
            }

def main():
    """Test the Tesseract backend"""
    backend = TesseractBackend(languages='ara+eng')
    
    # Test with a sample PDF
    pdf_path = "pdfs/نظام الإثبات.pdf"
    if os.path.exists(pdf_path):
        results = backend.extract_text_from_pdf(pdf_path, pages=[0, 1, 2])
        print(f"Extracted {results['total_words']} words with {results['overall_confidence']:.3f} confidence")
        print(f"First 200 characters: {results['full_text'][:200]}...")
    else:
        print(f"Test PDF not found: {pdf_path}")

if __name__ == "__main__":
    main()