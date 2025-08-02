"""
OCR Evaluation Framework
Comprehensive comparison system for multiple OCR backends
"""

import json
import logging
import time
import os
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures
from pathlib import Path

# Import OCR backends
from ocr.paddleocr_backend import PaddleOCRBackend
from ocr.easyocr_backend import EasyOCRBackend
from ocr.tesseract_backend import TesseractBackend
from ocr.trocr_backend import TrOCRBackend
from utils.logger import setup_logger

logger = logging.getLogger(__name__)

class OCREvaluationFramework:
    """Comprehensive OCR evaluation and comparison framework"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the OCR evaluation framework
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Available backends
        self.backends = {}
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize all available OCR backends"""
        logger.info("Initializing OCR backends...")
        
        # PaddleOCR
        try:
            self.backends['PaddleOCR'] = PaddleOCRBackend(lang='ar')
            logger.info("✓ PaddleOCR initialized")
        except Exception as e:
            logger.warning(f"✗ PaddleOCR failed to initialize: {e}")
        
        # EasyOCR
        try:
            self.backends['EasyOCR'] = EasyOCRBackend(languages=['ar', 'en'])
            logger.info("✓ EasyOCR initialized")
        except Exception as e:
            logger.warning(f"✗ EasyOCR failed to initialize: {e}")
        
        # Tesseract
        try:
            self.backends['Tesseract'] = TesseractBackend(languages='ara+eng')
            logger.info("✓ Tesseract initialized")
        except Exception as e:
            logger.warning(f"✗ Tesseract failed to initialize: {e}")
        
        # TrOCR
        try:
            self.backends['TrOCR'] = TrOCRBackend()
            logger.info("✓ TrOCR initialized")
        except Exception as e:
            logger.warning(f"✗ TrOCR failed to initialize: {e}")
        
        logger.info(f"Initialized {len(self.backends)} OCR backends: {list(self.backends.keys())}")
    
    def evaluate_single_backend(self, backend_name: str, pdf_path: str, 
                               pages: List[int] = None) -> Dict[str, Any]:
        """
        Evaluate a single OCR backend on a PDF
        
        Args:
            backend_name: Name of the backend to evaluate
            pdf_path: Path to the PDF file
            pages: List of page numbers to process
            
        Returns:
            Evaluation results dictionary
        """
        if backend_name not in self.backends:
            raise ValueError(f"Backend '{backend_name}' not available. Available: {list(self.backends.keys())}")
        
        backend = self.backends[backend_name]
        
        logger.info(f"Evaluating {backend_name} on {pdf_path}")
        start_time = time.time()
        
        try:
            # Extract text
            results = backend.extract_text_from_pdf(pdf_path, pages=pages)
            
            # Add evaluation metadata
            results['evaluation'] = {
                'backend_name': backend_name,
                'pdf_path': pdf_path,
                'pages_processed': pages or 'all',
                'evaluation_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error evaluating {backend_name}: {e}")
            return {
                'backend': backend_name,
                'evaluation': {
                    'backend_name': backend_name,
                    'pdf_path': pdf_path,
                    'pages_processed': pages or 'all',
                    'evaluation_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }
            }
    
    def compare_backends(self, pdf_path: str, pages: List[int] = None, 
                        backends: List[str] = None, parallel: bool = True) -> Dict[str, Any]:
        """
        Compare multiple OCR backends on the same PDF
        
        Args:
            pdf_path: Path to the PDF file
            pages: List of page numbers to process
            backends: List of backend names to compare (None for all available)
            parallel: Whether to run evaluations in parallel
            
        Returns:
            Comparison results dictionary
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Select backends to compare
        backends_to_test = backends or list(self.backends.keys())
        available_backends = [b for b in backends_to_test if b in self.backends]
        
        if not available_backends:
            raise ValueError("No available backends to test")
        
        logger.info(f"Comparing {len(available_backends)} backends: {available_backends}")
        logger.info(f"PDF: {pdf_path}, Pages: {pages or 'all'}")
        
        comparison_start = time.time()
        results = {}
        
        if parallel and len(available_backends) > 1:
            # Parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(available_backends)) as executor:
                future_to_backend = {
                    executor.submit(self.evaluate_single_backend, backend, pdf_path, pages): backend
                    for backend in available_backends
                }
                
                for future in concurrent.futures.as_completed(future_to_backend):
                    backend = future_to_backend[future]
                    try:
                        results[backend] = future.result()
                    except Exception as e:
                        logger.error(f"Error evaluating {backend}: {e}")
                        results[backend] = {'error': str(e)}
        else:
            # Sequential execution
            for backend in available_backends:
                results[backend] = self.evaluate_single_backend(backend, pdf_path, pages)
        
        # Generate comparison summary
        comparison_summary = self._generate_comparison_summary(results)
        
        comparison_results = {
            'comparison_metadata': {
                'pdf_path': pdf_path,
                'pages_processed': pages or 'all',
                'backends_compared': available_backends,
                'total_comparison_time': time.time() - comparison_start,
                'timestamp': datetime.now().isoformat(),
                'parallel_execution': parallel
            },
            'individual_results': results,
            'comparison_summary': comparison_summary
        }
        
        return comparison_results
    
    def _generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary comparing the results from different backends
        
        Args:
            results: Dictionary of results from different backends
            
        Returns:
            Comparison summary dictionary
        """
        summary = {
            'performance_ranking': [],
            'accuracy_ranking': [],
            'speed_ranking': [],
            'statistics': {}
        }
        
        # Extract metrics for comparison
        backend_metrics = []
        
        for backend_name, result in results.items():
            if 'error' in result:
                continue
                
            metrics = {
                'backend': backend_name,
                'total_words': result.get('total_words', 0),
                'overall_confidence': result.get('overall_confidence', 0.0),
                'processing_time': result.get('processing_time', float('inf')),
                'pages_per_second': result.get('total_pages', 0) / max(result.get('processing_time', 1), 0.001),
                'words_per_second': result.get('total_words', 0) / max(result.get('processing_time', 1), 0.001)
            }
            backend_metrics.append(metrics)
        
        if not backend_metrics:
            return summary
        
        # Rank by confidence (accuracy proxy)
        accuracy_sorted = sorted(backend_metrics, key=lambda x: x['overall_confidence'], reverse=True)
        summary['accuracy_ranking'] = [
            {
                'rank': i + 1,
                'backend': item['backend'],
                'confidence': item['overall_confidence'],
                'total_words': item['total_words']
            }
            for i, item in enumerate(accuracy_sorted)
        ]
        
        # Rank by speed (words per second)
        speed_sorted = sorted(backend_metrics, key=lambda x: x['words_per_second'], reverse=True)
        summary['speed_ranking'] = [
            {
                'rank': i + 1,
                'backend': item['backend'],
                'words_per_second': item['words_per_second'],
                'processing_time': item['processing_time']
            }
            for i, item in enumerate(speed_sorted)
        ]
        
        # Overall performance ranking (balanced score)
        for item in backend_metrics:
            # Normalize scores (0-1)
            max_confidence = max(m['overall_confidence'] for m in backend_metrics)
            max_speed = max(m['words_per_second'] for m in backend_metrics)
            
            normalized_confidence = item['overall_confidence'] / max(max_confidence, 0.001)
            normalized_speed = item['words_per_second'] / max(max_speed, 0.001)
            
            # Weighted score (60% accuracy, 40% speed)
            item['performance_score'] = 0.6 * normalized_confidence + 0.4 * normalized_speed
        
        performance_sorted = sorted(backend_metrics, key=lambda x: x['performance_score'], reverse=True)
        summary['performance_ranking'] = [
            {
                'rank': i + 1,
                'backend': item['backend'],
                'performance_score': item['performance_score'],
                'confidence': item['overall_confidence'],
                'speed': item['words_per_second']
            }
            for i, item in enumerate(performance_sorted)
        ]
        
        # Generate statistics
        summary['statistics'] = {
            'total_backends_tested': len(backend_metrics),
            'avg_confidence': sum(m['overall_confidence'] for m in backend_metrics) / len(backend_metrics),
            'avg_processing_time': sum(m['processing_time'] for m in backend_metrics) / len(backend_metrics),
            'avg_words_extracted': sum(m['total_words'] for m in backend_metrics) / len(backend_metrics),
            'best_accuracy': accuracy_sorted[0]['backend'] if accuracy_sorted else None,
            'fastest_backend': speed_sorted[0]['backend'] if speed_sorted else None,
            'best_overall': performance_sorted[0]['backend'] if performance_sorted else None
        }
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save evaluation results to a JSON file
        
        Args:
            results: Results dictionary to save
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ocr_evaluation_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            """Convert numpy types to JSON serializable types"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # Clean the results
        clean_results = convert_numpy_types(results)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        return str(filepath)
    
    def benchmark_all_backends(self, pdf_path: str, num_pages: int = 3) -> Dict[str, Any]:
        """
        Benchmark all available backends on a PDF
        
        Args:
            pdf_path: Path to the PDF file
            num_pages: Number of pages to benchmark
            
        Returns:
            Benchmark results dictionary
        """
        logger.info(f"Benchmarking all backends on {pdf_path} ({num_pages} pages)")
        
        benchmark_results = {}
        
        for backend_name, backend in self.backends.items():
            logger.info(f"Benchmarking {backend_name}...")
            try:
                benchmark_result = backend.benchmark_performance(pdf_path, num_pages)
                benchmark_results[backend_name] = benchmark_result
                logger.info(f"{backend_name}: {benchmark_result.get('words_per_second', 0):.2f} words/sec")
            except Exception as e:
                logger.error(f"Benchmark failed for {backend_name}: {e}")
                benchmark_results[backend_name] = {'error': str(e)}
        
        return benchmark_results

def main():
    """Main function to demonstrate the OCR evaluation framework"""
    # Setup logging
    setup_logger()
    
    # Initialize framework
    framework = OCREvaluationFramework()
    
    # Test PDF path
    pdf_path = "pdfs/نظام الإثبات.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Test PDF not found: {pdf_path}")
        print("Please place a PDF file at the specified path to test the framework.")
        return
    
    # Compare all backends on first 3 pages
    logger.info("Starting OCR backend comparison...")
    comparison_results = framework.compare_backends(
        pdf_path=pdf_path,
        pages=[0, 1, 2],
        parallel=True
    )
    
    # Save results
    output_file = framework.save_results(comparison_results, "ocr_comparison_results.json")
    
    # Print summary
    summary = comparison_results['comparison_summary']
    print("\n" + "="*60)
    print("OCR BACKEND COMPARISON RESULTS")
    print("="*60)
    
    print("\n🏆 OVERALL PERFORMANCE RANKING:")
    for item in summary['performance_ranking']:
        print(f"{item['rank']}. {item['backend']} - Score: {item['performance_score']:.3f}")
    
    print("\n🎯 ACCURACY RANKING (by confidence):")
    for item in summary['accuracy_ranking']:
        print(f"{item['rank']}. {item['backend']} - Confidence: {item['confidence']:.3f} ({item['total_words']} words)")
    
    print("\n⚡ SPEED RANKING:")
    for item in summary['speed_ranking']:
        print(f"{item['rank']}. {item['backend']} - {item['words_per_second']:.2f} words/sec")
    
    print(f"\n📊 STATISTICS:")
    stats = summary['statistics']
    print(f"Best Overall: {stats['best_overall']}")
    print(f"Most Accurate: {stats['best_accuracy']}")
    print(f"Fastest: {stats['fastest_backend']}")
    print(f"Average Confidence: {stats['avg_confidence']:.3f}")
    print(f"Average Words Extracted: {stats['avg_words_extracted']:.0f}")
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
