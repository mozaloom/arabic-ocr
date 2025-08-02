"""
TrOCR (Transformer-based OCR) backend for text extraction from PDFs
Uses Microsoft's TrOCR model for text recognition
"""

import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
import logging
import time
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TrOCRBackend:
    """TrOCR implementation for PDF text extraction"""
    
    def __init__(self, model_name="microsoft/trocr-base-printed", device=None):
        """
        Initialize TrOCR backend
        
        Args:
            model_name: Hugging Face model name for TrOCR
            device: Device to run the model on ('cpu', 'cuda', or None for auto)
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.processor = None
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the TrOCR model and processor"""
        try:
            logger.info(f"Initializing TrOCR model: {self.model_name}")
            logger.info(f"Using device: {self.device}")
            
            # Load processor and model
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            
            logger.info("TrOCR model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TrOCR model: {e}")
            raise
    
    def _extract_text_from_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract text from a single image using TrOCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary containing extracted text and confidence
        """
        try:
            # Preprocess the image
            pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
            
            # Decode the generated text
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # TrOCR doesn't provide confidence scores directly, so we use a placeholder
            # In practice, you might implement confidence estimation based on model outputs
            confidence = 0.85  # Placeholder confidence score
            
            return {
                'text': generated_text.strip(),
                'confidence': confidence,
                'bbox': [0, 0, image.width, image.height]  # Full image bbox
            }
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'bbox': [0, 0, 0, 0],
                'error': str(e)
            }
    
    def _split_image_into_regions(self, image: Image.Image, num_regions: int = 4) -> List[Image.Image]:
        """
        Split image into regions for better text extraction
        
        Args:
            image: PIL Image object
            num_regions: Number of horizontal regions to split into
            
        Returns:
            List of image regions
        """
        width, height = image.size
        region_height = height // num_regions
        regions = []
        
        for i in range(num_regions):
            top = i * region_height
            bottom = min((i + 1) * region_height, height)
            region = image.crop((0, top, width, bottom))
            regions.append(region)
        
        return regions
    
    def extract_text_from_pdf(self, pdf_path: str, pages: List[int] = None, 
                             dpi: int = 200, split_regions: bool = True) -> Dict[str, Any]:
        """
        Extract text from PDF using TrOCR
        
        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process (0-indexed). If None, process all pages
            dpi: DPI for PDF to image conversion
            split_regions: Whether to split pages into regions for better processing
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.processor is None or self.model is None:
            self._initialize_model()
        
        start_time = time.time()
        results = {
            'full_text': '',
            'page_results': [],
            'total_pages': 0,
            'total_words': 0,
            'overall_confidence': 0.0,
            'processing_time': 0.0,
            'backend': 'TrOCR'
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
                
                page_text_parts = []
                page_confidences = []
                raw_results = []
                
                if split_regions:
                    # Split image into regions for better processing
                    regions = self._split_image_into_regions(image, num_regions=4)
                    
                    for region_idx, region in enumerate(regions):
                        result = self._extract_text_from_image(region)
                        if result['text']:
                            page_text_parts.append(result['text'])
                            page_confidences.append(result['confidence'])
                            raw_results.append({
                                'region': region_idx,
                                'text': result['text'],
                                'confidence': result['confidence'],
                                'bbox': result['bbox']
                            })
                else:
                    # Process full image
                    result = self._extract_text_from_image(image)
                    if result['text']:
                        page_text_parts.append(result['text'])
                        page_confidences.append(result['confidence'])
                        raw_results.append({
                            'text': result['text'],
                            'confidence': result['confidence'],
                            'bbox': result['bbox']
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
            
            logger.info(f"TrOCR extraction completed: {results['total_words']} words, "
                       f"overall confidence: {results['overall_confidence']:.3f}, "
                       f"time: {results['processing_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during TrOCR text extraction: {e}")
            raise
    
    def benchmark_performance(self, pdf_path: str, num_pages: int = 3) -> Dict[str, float]:
        """
        Benchmark the performance of TrOCR on the given PDF
        
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
                'backend': 'TrOCR'
            }
        except Exception as e:
            logger.error(f"Error during TrOCR benchmarking: {e}")
            return {
                'processing_time': float('inf'),
                'pages_per_second': 0,
                'words_per_second': 0,
                'average_confidence': 0,
                'total_words': 0,
                'backend': 'TrOCR',
                'error': str(e)
            }

def main():
    """Test the TrOCR backend"""
    backend = TrOCRBackend()
    
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