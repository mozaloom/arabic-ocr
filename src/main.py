"""
Main entry point for the OCR Text Extraction Application
Comprehensive OCR evaluation framework for Arabic/English PDF processing
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logger
from utils.file_handler import detect_pdf_type
from ocr_evaluation import OCREvaluationFramework

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="OCR Text Extraction and Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --pdf "document.pdf" --compare --pages 0 1 2
  python main.py --pdf "document.pdf" --backend PaddleOCR
  python main.py --pdf "document.pdf" --benchmark --pages 3
  python main.py --demo
        """
    )
    
    parser.add_argument(
        '--pdf', 
        type=str,
        default="pdfs/نظام الإثبات.pdf",
        help='Path to PDF file to process'
    )
    
    parser.add_argument(
        '--backend', 
        type=str,
        choices=['PaddleOCR', 'EasyOCR', 'Tesseract', 'TrOCR'],
        help='Specific OCR backend to use'
    )
    
    parser.add_argument(
        '--compare', 
        action='store_true',
        help='Compare all available OCR backends'
    )
    
    parser.add_argument(
        '--benchmark', 
        action='store_true',
        help='Run performance benchmarks'
    )
    
    parser.add_argument(
        '--pages', 
        type=int, 
        nargs='+',
        default=[0, 1, 2],
        help='Page numbers to process (0-indexed)'
    )
    
    parser.add_argument(
        '--output', 
        type=str,
        default='output',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='Run demonstration with built-in test data'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(level=log_level)
    
    # Print banner
    print_banner()
    
    if args.demo:
        run_demo()
        return
    
    # Check if PDF exists
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        print(f"❌ PDF file not found: {args.pdf}")
        print("Please provide a valid PDF path or use --demo to run with test data.")
        return 1
    
    # Analyze PDF type
    logger.info(f"Analyzing PDF: {args.pdf}")
    pdf_type = detect_pdf_type(args.pdf)
    print(f"📄 PDF Type: {pdf_type}")
    
    # Initialize framework
    framework = OCREvaluationFramework(output_dir=args.output)
    
    if args.compare:
        # Compare all backends
        print(f"🔍 Comparing OCR backends on pages {args.pages}...")
        results = framework.compare_backends(
            pdf_path=args.pdf,
            pages=args.pages,
            parallel=True
        )
        
        # Save and display results
        output_file = framework.save_results(results, "comparison_results.json")
        display_comparison_results(results)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    elif args.benchmark:
        # Run benchmarks
        print(f"⚡ Benchmarking OCR backends on {len(args.pages)} pages...")
        benchmark_results = framework.benchmark_all_backends(
            pdf_path=args.pdf,
            num_pages=len(args.pages)
        )
        
        output_file = framework.save_results(benchmark_results, "benchmark_results.json")
        display_benchmark_results(benchmark_results)
        print(f"\n💾 Benchmark results saved to: {output_file}")
        
    elif args.backend:
        # Use specific backend
        print(f"🔍 Processing with {args.backend} backend...")
        results = framework.evaluate_single_backend(
            backend_name=args.backend,
            pdf_path=args.pdf,
            pages=args.pages
        )
        
        output_file = framework.save_results(results, f"{args.backend.lower()}_results.json")
        display_single_backend_results(results)
        print(f"\n💾 Results saved to: {output_file}")
        
    else:
        # Default: compare all backends
        print("🔍 Running default comparison of all OCR backends...")
        results = framework.compare_backends(
            pdf_path=args.pdf,
            pages=args.pages,
            parallel=True
        )
        
        output_file = framework.save_results(results, "default_comparison.json")
        display_comparison_results(results)
        print(f"\n💾 Results saved to: {output_file}")

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                OCR Text Extraction Framework                 ║
║          Comprehensive Arabic/English PDF Processing         ║
║                                                              ║
║  🔍 Multi-Backend OCR Comparison                             ║
║  📊 Performance Benchmarking                                 ║
║  🌍 Arabic & English Support                                 ║
║  ⚡ Parallel Processing                                       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def display_comparison_results(results):
    """Display comparison results in a user-friendly format"""
    summary = results.get('comparison_summary', {})
    
    print("\n" + "="*60)
    print("📊 OCR BACKEND COMPARISON RESULTS")
    print("="*60)
    
    # Performance ranking
    performance_ranking = summary.get('performance_ranking', [])
    if performance_ranking:
        print("\n🏆 OVERALL PERFORMANCE RANKING:")
        for item in performance_ranking:
            score = item.get('performance_score', 0)
            confidence = item.get('confidence', 0)
            speed = item.get('speed', 0)
            print(f"  {item.get('rank', 0)}. {item.get('backend', 'Unknown')} "
                  f"(Score: {score:.3f}, Confidence: {confidence:.3f}, Speed: {speed:.1f} w/s)")
    
    # Accuracy ranking
    accuracy_ranking = summary.get('accuracy_ranking', [])
    if accuracy_ranking:
        print("\n🎯 ACCURACY RANKING:")
        for item in accuracy_ranking:
            confidence = item.get('confidence', 0)
            words = item.get('total_words', 0)
            print(f"  {item.get('rank', 0)}. {item.get('backend', 'Unknown')} "
                  f"- Confidence: {confidence:.3f} ({words} words)")
    
    # Speed ranking
    speed_ranking = summary.get('speed_ranking', [])
    if speed_ranking:
        print("\n⚡ SPEED RANKING:")
        for item in speed_ranking:
            speed = item.get('words_per_second', 0)
            time_taken = item.get('processing_time', 0)
            print(f"  {item.get('rank', 0)}. {item.get('backend', 'Unknown')} "
                  f"- {speed:.2f} words/sec ({time_taken:.2f}s)")
    
    # Statistics
    stats = summary.get('statistics', {})
    if stats:
        print("\n📈 SUMMARY STATISTICS:")
        print(f"  Best Overall: {stats.get('best_overall', 'N/A')}")
        print(f"  Most Accurate: {stats.get('best_accuracy', 'N/A')}")
        print(f"  Fastest: {stats.get('fastest_backend', 'N/A')}")
        print(f"  Average Confidence: {stats.get('avg_confidence', 0):.3f}")
        print(f"  Average Words: {stats.get('avg_words_extracted', 0):.0f}")

def display_benchmark_results(results):
    """Display benchmark results"""
    print("\n" + "="*60)
    print("⚡ OCR BACKEND BENCHMARK RESULTS")
    print("="*60)
    
    for backend_name, result in results.items():
        if 'error' in result:
            print(f"\n❌ {backend_name}: {result['error']}")
            continue
            
        print(f"\n✅ {backend_name}:")
        print(f"  Processing Time: {result.get('processing_time', 0):.2f}s")
        print(f"  Pages/Second: {result.get('pages_per_second', 0):.2f}")
        print(f"  Words/Second: {result.get('words_per_second', 0):.2f}")
        print(f"  Average Confidence: {result.get('average_confidence', 0):.3f}")
        print(f"  Total Words: {result.get('total_words', 0)}")

def display_single_backend_results(results):
    """Display results from a single backend"""
    backend = results.get('backend', 'Unknown')
    
    print(f"\n📊 {backend} RESULTS")
    print("="*50)
    print(f"Total Pages: {results.get('total_pages', 0)}")
    print(f"Total Words: {results.get('total_words', 0)}")
    print(f"Overall Confidence: {results.get('overall_confidence', 0):.3f}")
    print(f"Processing Time: {results.get('processing_time', 0):.2f}s")
    
    # Show first 200 characters of extracted text
    full_text = results.get('full_text', '')
    if full_text:
        print(f"\n📝 Text Preview (first 200 chars):")
        print(f"'{full_text[:200]}...'")

def run_demo():
    """Run a demonstration of the OCR framework"""
    print("🚀 Running OCR Framework Demo...")
    
    # Check for test PDF
    test_pdf = "pdfs/نظام الإثبات.pdf"
    if not os.path.exists(test_pdf):
        print(f"❌ Demo PDF not found: {test_pdf}")
        print("Please place a test PDF file at the specified path.")
        return
    
    # Initialize framework
    framework = OCREvaluationFramework(output_dir="demo_output")
    
    print(f"📄 Testing with: {test_pdf}")
    print("🔍 Comparing all available OCR backends on first 3 pages...")
    
    # Run comparison
    results = framework.compare_backends(
        pdf_path=test_pdf,
        pages=[0, 1, 2],
        parallel=True
    )
    
    # Save and display results
    output_file = framework.save_results(results, "demo_results.json")
    display_comparison_results(results)
    
    print(f"\n🎉 Demo completed! Results saved to: {output_file}")
    print("\nYou can now:")
    print("  • Review the detailed JSON results")
    print("  • Try different backends with --backend option")
    print("  • Run benchmarks with --benchmark option")
    print("  • Process different page ranges with --pages option")

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)