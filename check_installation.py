#!/usr/bin/env python3
"""
Installation and dependency checker for OCR Text Extraction Framework
"""

import sys
import subprocess
import importlib
import platform
import os
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_python_version():
    """Check Python version requirements"""
    print_header("Python Version Check")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        return False
    else:
        print("✅ Python version is compatible")
        return True

def check_system_dependencies():
    """Check system-level dependencies"""
    print_header("System Dependencies Check")
    
    system = platform.system().lower()
    dependencies = []
    
    # Check Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract: {version}")
        else:
            print("❌ Tesseract: Not found or not working")
            dependencies.append("tesseract-ocr")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Tesseract: Not installed")
        dependencies.append("tesseract-ocr")
    
    # Check Poppler (pdf2image dependency)
    try:
        result = subprocess.run(['pdftoppm', '-h'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Poppler (pdftoppm): Available")
        else:
            print("❌ Poppler: Not found")
            dependencies.append("poppler-utils")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Poppler: Not installed")
        dependencies.append("poppler-utils")
    
    if dependencies:
        print(f"\n📋 Missing system dependencies: {', '.join(dependencies)}")
        print("\n🔧 Installation commands:")
        
        if system == "linux":
            print(f"   sudo apt-get install {' '.join(dependencies)}")
            if "tesseract-ocr" in dependencies:
                print("   sudo apt-get install tesseract-ocr-ara tesseract-ocr-eng")
        elif system == "darwin":  # macOS
            deps_map = {"tesseract-ocr": "tesseract tesseract-lang", "poppler-utils": "poppler"}
            brew_deps = [deps_map.get(dep, dep) for dep in dependencies]
            print(f"   brew install {' '.join(brew_deps)}")
        elif system == "windows":
            print("   Download and install manually:")
            if "tesseract-ocr" in dependencies:
                print("   - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
            if "poppler-utils" in dependencies:
                print("   - Poppler: https://poppler.freedesktop.org/")
        
        return False
    else:
        print("✅ All system dependencies are available")
        return True

def check_python_packages():
    """Check Python package dependencies"""
    print_header("Python Packages Check")
    
    required_packages = [
        ('numpy', 'numpy'),
        ('PIL', 'Pillow'),
        ('pdf2image', 'pdf2image'),
        ('cv2', 'opencv-python'),
    ]
    
    optional_packages = [
        ('paddleocr', 'paddleocr'),
        ('easyocr', 'easyocr'),
        ('pytesseract', 'pytesseract'),
        ('torch', 'torch'),
        ('transformers', 'transformers'),
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for import_name, package_name in required_packages:
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name}: Available")
        except ImportError:
            print(f"❌ {package_name}: Missing")
            missing_required.append(package_name)
    
    # Check optional packages (OCR backends)
    for import_name, package_name in optional_packages:
        try:
            importlib.import_module(import_name)
            print(f"✅ {package_name}: Available")
        except ImportError:
            print(f"⚠️  {package_name}: Missing (optional)")
            missing_optional.append(package_name)
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print(f"   Install with: pip install {' '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print(f"   Install with: pip install {' '.join(missing_optional)}")
        print("   (These are needed for specific OCR backends)")
    
    print("✅ All required Python packages are available")
    return True

def check_project_structure():
    """Check project directory structure"""
    print_header("Project Structure Check")
    
    current_dir = Path.cwd()
    expected_dirs = ['src', 'src/ocr', 'src/utils', 'src/extraction']
    expected_files = [
        'src/main.py',
        'src/config.py',
        'src/ocr_evaluation.py',
        'requirements.txt'
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in expected_dirs:
        full_path = current_dir / dir_path
        if full_path.exists():
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Directory: {dir_path}")
            missing_dirs.append(dir_path)
    
    for file_path in expected_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ File: {file_path}")
            missing_files.append(file_path)
    
    # Check/create output directories
    output_dirs = ['output', 'logs', 'pdfs']
    for dir_name in output_dirs:
        dir_path = current_dir / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✅ Created directory: {dir_name}")
            except Exception as e:
                print(f"❌ Cannot create directory {dir_name}: {e}")
        else:
            print(f"✅ Directory exists: {dir_name}")
    
    if missing_dirs or missing_files:
        print(f"\n❌ Missing project components:")
        if missing_dirs:
            print(f"   Directories: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"   Files: {', '.join(missing_files)}")
        return False
    
    print("✅ Project structure is complete")
    return True

def test_basic_functionality():
    """Test basic framework functionality"""
    print_header("Basic Functionality Test")
    
    try:
        # Test imports
        sys.path.append('src')
        from utils.file_handler import detect_pdf_type
        from config import OCR_BACKENDS
        print("✅ Core modules import successfully")
        
        # Test configuration
        available_backends = [name for name, config in OCR_BACKENDS.items() if config.get('enabled', True)]
        print(f"✅ Available OCR backends: {', '.join(available_backends)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Main installation checker"""
    print("🔍 OCR Text Extraction Framework - Installation Checker")
    print(f"Running on: {platform.system()} {platform.release()}")
    
    checks = [
        ("Python Version", check_python_version),
        ("System Dependencies", check_system_dependencies),
        ("Python Packages", check_python_packages),
        ("Project Structure", check_project_structure),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append((check_name, False))
    
    # Summary
    print_header("Installation Check Summary")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Installation is complete! You can now run the OCR framework.")
        print("\nQuick start:")
        print("  python src/main.py --demo")
        return 0
    else:
        print(f"\n⚠️  {total - passed} issues need to be resolved before using the framework.")
        print("Please follow the installation instructions above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
