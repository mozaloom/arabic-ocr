"""
EasyOCR backend for text extraction from PDFs
Supports Arabic and English text recognition
"""

import easyocr
import numpy as np
from pdf2image import convert_from_path
import logging
import time
from typing import List, Dict, Any, Tuple
import os

logger = logging.getLogger(__name__)

class EasyOCRBackend:
    """EasyOCR implementation for PDF text extraction"""
    
    def __init__(self, languages=['ar', 'en'], gpu=False):
        """
        Initialize EasyOCR backend
        
        Args:
            languages: List of language codes (e.g., ['ar', 'en'])
            gpu: Whether to use GPU acceleration
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialize the EasyOCR reader"""
        try:
            logger.info(f"Initializing EasyOCR with languages: {self.languages}")
            self.reader = easyocr.Reader(
                lang_list=self.languages,
                gpu=self.gpu,
                verbose=False
            )
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str, pages: List[int] = None, 
                             dpi: int = 200, confidence_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Extract text from PDF using EasyOCR
        
        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (0-indexed). If None, process all pages
            dpi: DPI for PDF to image conversion
            confidence_threshold: Minimum confidence threshold for text detection
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.reader is None:
            self._initialize_reader()
        
        start_time = time.time()
        results = {
            'full_text': '',
            'page_results': [],
            'total_pages': 0,
            'total_words': 0,
            'overall_confidence': 0.0,
            'processing_time': 0.0,
            'backend': 'EasyOCR'
        }
        
        try:
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
                
                # Convert PIL image to numpy array
                image_np = np.array(image)
                
                # Extract text using EasyOCR
                ocr_results = self.reader.readtext(
                    image_np,
                    paragraph=False,
                    width_ths=0.7,
                    height_ths=0.7
                )
                
                # Process results
                page_text_parts = []
                page_confidences = []
                raw_results = []
                
                for (bbox, text, confidence) in ocr_results:
                    if confidence >= confidence_threshold:
                        page_text_parts.append(text)
                        page_confidences.append(confidence)
                        raw_results.append({
                            'bbox': bbox,
                            'text': text,
                            'confidence': confidence
                        })
                
                page_text = ' '.join(page_text_parts)
                page_word_count = len(page_text.split()) if page_text.strip() else 0
                page_avg_confidence = np.mean(page_confidences) if page_confidences else 0.0
                
                # Store page results
                page_result = {
                    'page_number': actual_page_num + 1,
                    'text': page_text,
                    'word_count': page_word_count,
                    'avg_confidence': float(page_avg_confidence),
                    'raw_result': raw_results
                }
                
                results['page_results'].append(page_result)
                page_texts.append(f"--- Page {actual_page_num + 1} ---\n{page_text}")
                
                if page_confidences:
                    all_confidences.extend(page_confidences)
                
                logger.info(f"Page {actual_page_num + 1}: {page_word_count} words, "
                           f"avg confidence: {page_avg_confidence:.3f}")
            
            # Combine results
            results['full_text'] = '\n'.join(page_texts)
            results['total_words'] = sum(page['word_count'] for page in results['page_results'])
            results['overall_confidence'] = float(np.mean(all_confidences)) if all_confidences else 0.0
            results['processing_time'] = time.time() - start_time
            
            logger.info(f"EasyOCR extraction completed: {results['total_words']} words, "
                       f"overall confidence: {results['overall_confidence']:.3f}, "
                       f"time: {results['processing_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during EasyOCR text extraction: {e}")
            raise
    
    def benchmark_performance(self, pdf_path: str, num_pages: int = 3) -> Dict[str, float]:
        """
        Benchmark the performance of EasyOCR on the given PDF
        
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
                'backend': 'EasyOCR'
            }
        except Exception as e:
            logger.error(f"Error during EasyOCR benchmarking: {e}")
            return {
                'processing_time': float('inf'),
                'pages_per_second': 0,
                'words_per_second': 0,
                'average_confidence': 0,
                'total_words': 0,
                'backend': 'EasyOCR',
                'error': str(e)
            }

def main():
    """Test the EasyOCR backend"""
    backend = EasyOCRBackend(languages=['ar', 'en'])
    
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