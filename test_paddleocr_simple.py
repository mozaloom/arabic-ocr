# Simple test to understand PaddleOCR predict API
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import json

# Initialize PaddleOCR
ocr = PaddleOCR(use_textline_orientation=True, lang='en')

# Convert first page of PDF to image for testing
pdf_path = "pdfs/النظام الجزائي لجرائم التزوير.pdf"
images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)  # Only first page, lower DPI

if images:
    # Save the first page as a test image
    test_image = "test_page.jpg"
    images[0].save(test_image, 'JPEG')
    
    print("Running OCR on test image...")
    
    # Test the predict method
    try:
        result = ocr.predict(input=test_image)
        print("Result type:", type(result))
        print("Result length:", len(result) if hasattr(result, '__len__') else 'No length')
        
        # Save raw result to understand structure
        with open("raw_result.json", "w", encoding="utf-8") as f:
            try:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            except:
                f.write(str(result))
        
        print("Raw result saved to raw_result.json")
        
        # Try to extract text
        if result:
            for i, page_result in enumerate(result):
                print(f"Page {i} result type:", type(page_result))
                print(f"Page {i} attributes:", [attr for attr in dir(page_result) if not attr.startswith('_')])
                
                # Try different ways to access text
                if hasattr(page_result, 'text'):
                    print(f"Text attribute: {page_result.text}")
                if hasattr(page_result, 'get_text'):
                    print(f"get_text method: {page_result.get_text()}")
                
                break  # Just check first result
                
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No images extracted from PDF")
