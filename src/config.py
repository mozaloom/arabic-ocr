"""
Configuration settings for the OCR Text Extraction Framework
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "output"
PDFS_DIR = PROJECT_ROOT / "pdfs"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# OCR Backend configurations
OCR_BACKENDS = {
    'PaddleOCR': {
        'enabled': True,
        'languages': ['ar', 'en'],
        'use_gpu': False,
        'use_angle_cls': True,
        'use_space_char': True,
        'confidence_threshold': 0.3,
        'default_dpi': 150
    },
    'EasyOCR': {
        'enabled': True,
        'languages': ['ar', 'en'],
        'use_gpu': False,
        'confidence_threshold': 0.3,
        'default_dpi': 200,
        'width_ths': 0.7,
        'height_ths': 0.7
    },
    'Tesseract': {
        'enabled': True,
        'languages': 'ara+eng',
        'psm': 6,  # Page Segmentation Mode
        'oem': 3,  # OCR Engine Mode
        'confidence_threshold': 0.3,
        'default_dpi': 200,
        'tesseract_cmd': None  # Auto-detect
    },
    'TrOCR': {
        'enabled': True,
        'model_name': 'microsoft/trocr-base-printed',
        'device': 'auto',  # 'cpu', 'cuda', or 'auto'
        'confidence_threshold': 0.5,
        'default_dpi': 200,
        'split_regions': True,
        'num_regions': 4
    }
}

# PDF processing settings
PDF_SETTINGS = {
    'default_dpi': 200,
    'max_dpi': 300,
    'min_dpi': 150,
    'image_format': 'RGB',
    'poppler_path': None,  # Auto-detect
    'temp_dir': None  # Use system temp
}

# Evaluation settings
EVALUATION_SETTINGS = {
    'default_pages': [0, 1, 2],  # First 3 pages
    'max_pages_benchmark': 5,
    'parallel_processing': True,
    'max_workers': 4,
    'timeout_per_page': 300,  # 5 minutes per page
    'save_intermediate_results': True
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'min_confidence': 0.5,
    'min_words_per_page': 10,
    'max_processing_time_per_page': 60,  # seconds
    'memory_limit_mb': 2048
}

# Output settings
OUTPUT_SETTINGS = {
    'save_raw_results': True,
    'save_images': False,  # Save intermediate images
    'image_format': 'PNG',
    'json_indent': 2,
    'encoding': 'utf-8'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_logging': True,
    'console_logging': True,
    'log_file': LOGS_DIR / 'ocr_framework.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Azure deployment settings (for future use)
AZURE_SETTINGS = {
    'enabled': False,
    'container_registry': '',
    'resource_group': '',
    'app_service_plan': '',
    'storage_account': '',
    'key_vault': '',
    'application_insights': '',
    'region': 'East US'
}

# Language-specific settings
LANGUAGE_SETTINGS = {
    'arabic': {
        'rtl': True,
        'font_family': 'Arial Unicode MS',
        'text_direction': 'rtl',
        'default_encoding': 'utf-8'
    },
    'english': {
        'rtl': False,
        'font_family': 'Arial',
        'text_direction': 'ltr',
        'default_encoding': 'utf-8'
    }
}

# Model download settings
MODEL_SETTINGS = {
    'cache_dir': PROJECT_ROOT / '.cache' / 'models',
    'download_timeout': 300,  # 5 minutes
    'retry_attempts': 3,
    'check_updates': False
}

# Environment-specific overrides
def load_environment_config():
    """Load environment-specific configuration overrides"""
    env_config = {}
    
    # Check for environment variables
    if os.getenv('OCR_DEBUG'):
        LOGGING_CONFIG['level'] = 'DEBUG'
    
    if os.getenv('OCR_GPU'):
        for backend in OCR_BACKENDS.values():
            if 'use_gpu' in backend:
                backend['use_gpu'] = True
    
    if os.getenv('OCR_OUTPUT_DIR'):
        global OUTPUT_DIR
        OUTPUT_DIR = Path(os.getenv('OCR_OUTPUT_DIR'))
        OUTPUT_DIR.mkdir(exist_ok=True)
    
    if os.getenv('TESSERACT_CMD'):
        OCR_BACKENDS['Tesseract']['tesseract_cmd'] = os.getenv('TESSERACT_CMD')
    
    return env_config

# Validation functions
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check if required directories exist and are writable
    for dir_path in [OUTPUT_DIR, LOGS_DIR]:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_path}: {e}")
        
        if not os.access(dir_path, os.W_OK):
            errors.append(f"Directory {dir_path} is not writable")
    
    # Validate DPI settings
    for backend, config in OCR_BACKENDS.items():
        if 'default_dpi' in config:
            dpi = config['default_dpi']
            if not (PDF_SETTINGS['min_dpi'] <= dpi <= PDF_SETTINGS['max_dpi']):
                errors.append(f"{backend} DPI {dpi} outside valid range")
    
    # Validate language settings
    for backend, config in OCR_BACKENDS.items():
        if backend == 'Tesseract' and 'languages' in config:
            # Check if language codes are valid
            valid_codes = ['ara', 'eng', 'ara+eng', 'eng+ara']
            if config['languages'] not in valid_codes:
                errors.append(f"Invalid Tesseract language code: {config['languages']}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    return True

# Initialize configuration on import
try:
    load_environment_config()
    validate_config()
except Exception as e:
    print(f"Warning: Configuration validation failed: {e}")

# Export commonly used paths and settings
__all__ = [
    'PROJECT_ROOT', 'SRC_DIR', 'OUTPUT_DIR', 'PDFS_DIR', 'LOGS_DIR',
    'OCR_BACKENDS', 'PDF_SETTINGS', 'EVALUATION_SETTINGS',
    'PERFORMANCE_THRESHOLDS', 'OUTPUT_SETTINGS', 'LOGGING_CONFIG',
    'AZURE_SETTINGS', 'LANGUAGE_SETTINGS', 'MODEL_SETTINGS'
]