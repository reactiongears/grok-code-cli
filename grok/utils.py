"""
Utility functions for file operations
"""

import os
import mimetypes
import chardet
from pathlib import Path
from typing import Optional, List, Tuple, Union

from .constants import (
    BINARY_SIGNATURES, TEXT_FILE_EXTENSIONS, 
    ENCODING_DETECTION_ORDER, MAX_FILE_SIZE_READ
)


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(8192)  # Read first 8KB
            
        # Try chardet detection
        result = chardet.detect(raw_data)
        if result['confidence'] > 0.8:
            return result['encoding']
        
        # Fallback to manual detection
        for encoding in ENCODING_DETECTION_ORDER:
            try:
                raw_data.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
                
        return 'utf-8'  # Default fallback
        
    except Exception:
        return 'utf-8'


def is_binary_file(file_path: Path) -> bool:
    """Check if file is binary"""
    try:
        # Check file extension first
        if file_path.suffix.lower() in TEXT_FILE_EXTENSIONS:
            return False
            
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return False
            
        # Check binary signatures
        with open(file_path, 'rb') as f:
            header = f.read(512)
            
        for signature in BINARY_SIGNATURES:
            if header.startswith(signature):
                return True
                
        # Check for null bytes (common in binary files)
        if b'\x00' in header:
            return True
            
        # Check for high ratio of non-printable characters
        printable_chars = sum(1 for byte in header if 32 <= byte <= 126)
        if len(header) > 0 and printable_chars / len(header) < 0.7:
            return True
            
        return False
        
    except Exception:
        return True  # Assume binary if can't determine


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def safe_file_read(file_path: Path, max_size: int = MAX_FILE_SIZE_READ) -> Tuple[str, str]:
    """Safely read file content with encoding detection"""
    try:
        # Check file size
        if file_path.stat().st_size > max_size:
            raise ValueError(f"File too large: {format_file_size(file_path.stat().st_size)}")
            
        # Check if binary
        if is_binary_file(file_path):
            raise ValueError("Cannot read binary file")
            
        # Detect encoding and read
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            
        return content, encoding
        
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")


def match_patterns(filename: str, patterns: List[str]) -> bool:
    """Check if filename matches any of the given patterns"""
    import fnmatch
    
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False