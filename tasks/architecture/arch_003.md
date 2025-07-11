# Architecture: Task 003 - Implement File Operations Tool Suite

## Overview
This task implements a comprehensive file operations toolkit that provides secure, efficient file handling capabilities. The tools will integrate with the security framework and provide the foundation for advanced development workflows.

## Technical Scope

### Files to Modify
- `grok/tools.py` - Add new file operation tools
- `grok/file_operations.py` - New dedicated file operations module
- `grok/utils.py` - New utility functions module
- `grok/constants.py` - New constants and configuration module

### Dependencies
- Task 001 (Import Fixes) - Required for stable imports
- Task 002 (Security Framework) - Required for secure file operations

## Architectural Approach

### 1. File Operations Architecture
```
File Operations Layer
    ↓
Security Validation Layer (from Task 002)
    ↓
File System Abstraction Layer
    ↓
Native File System Operations
```

### 2. Tool Components

#### A. File Reader (`read_file`)
- Text file reading with encoding detection
- Binary file detection and handling
- Line number support
- Size limits and safety checks

#### B. Directory Lister (`list_files`)
- Directory traversal with filtering
- Recursive and non-recursive options
- Hidden file handling
- Metadata extraction

#### C. File Finder (`find_files`)
- Pattern matching (glob and regex)
- Multi-criteria search
- Performance optimization
- Result sorting and filtering

#### D. Content Searcher (`grep_files`)
- Text pattern searching
- Regular expression support
- Context lines and formatting
- Performance optimization for large files

## Implementation Details

### Phase 1: Core File Operations Module

#### Create `grok/constants.py`
```python
"""
Constants and configuration for file operations
"""

# File size limits (in bytes)
MAX_FILE_SIZE_READ = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE_DISPLAY = 1 * 1024 * 1024  # 1MB for display
MAX_TOTAL_FILES_SCAN = 10000  # Maximum files to scan in operations

# Supported text file extensions
TEXT_FILE_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx',
    '.html', '.css', '.scss', '.sass', '.less', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.svg', '.csv', '.log', '.sh', '.bash',
    '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.java',
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs',
    '.go', '.rs', '.rb', '.php', '.pl', '.r', '.sql',
    '.dockerfile', '.gitignore', '.gitattributes',
    '.env', '.example', '.sample', '.template'
}

# Binary file signatures (magic numbers)
BINARY_SIGNATURES = [
    b'\x7fELF',     # ELF executable
    b'\x89PNG',     # PNG image
    b'\xff\xd8',    # JPEG image
    b'GIF8',        # GIF image
    b'PK\x03\x04',  # ZIP archive
    b'\x1f\x8b',    # GZIP archive
    b'BM',          # BMP image
    b'\x00\x00\x01\x00',  # ICO image
]

# Encoding detection order
ENCODING_DETECTION_ORDER = ['utf-8', 'utf-16', 'latin-1', 'ascii']

# Performance limits
MAX_GREP_CONTEXT_LINES = 10
MAX_FIND_RESULTS = 1000
MAX_DIRECTORY_DEPTH = 20
```

#### Create `grok/utils.py`
```python
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
```

#### Create `grok/file_operations.py`
```python
"""
File operations tools for Grok CLI
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass

from .security import SecurityManager
from .utils import safe_file_read, is_binary_file, format_file_size, match_patterns
from .constants import MAX_FIND_RESULTS, MAX_DIRECTORY_DEPTH, MAX_GREP_CONTEXT_LINES

@dataclass
class FileInfo:
    """File information data structure"""
    path: str
    name: str
    size: int
    size_formatted: str
    is_directory: bool
    is_binary: bool
    modified_time: float
    permissions: str

@dataclass
class SearchResult:
    """Search result data structure"""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str]
    context_after: List[str]

class FileOperations:
    """File operations toolkit"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
    
    def read_file(self, file_path: str, show_line_numbers: bool = False,
                  start_line: int = 1, max_lines: Optional[int] = None) -> Dict:
        """Read file content with optional line numbers"""
        try:
            path = Path(file_path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(path), 'read'):
                self.security.log_security_event('file_read_denied', {'path': str(path)})
                return {'error': 'File access denied for security reasons'}
            
            # Check if file exists
            if not path.exists():
                return {'error': f'File not found: {file_path}'}
            
            if path.is_dir():
                return {'error': f'Path is a directory: {file_path}'}
            
            # Read file content
            content, encoding = safe_file_read(path)
            lines = content.splitlines()
            
            # Apply line range filtering
            if start_line > 1:
                lines = lines[start_line-1:]
            
            if max_lines:
                lines = lines[:max_lines]
            
            # Format output
            if show_line_numbers:
                formatted_lines = []
                for i, line in enumerate(lines, start=start_line):
                    formatted_lines.append(f"{i:4d}: {line}")
                formatted_content = '\n'.join(formatted_lines)
            else:
                formatted_content = '\n'.join(lines)
            
            return {
                'success': True,
                'content': formatted_content,
                'encoding': encoding,
                'total_lines': len(content.splitlines()),
                'displayed_lines': len(lines),
                'file_size': format_file_size(path.stat().st_size)
            }
            
        except Exception as e:
            self.security.log_security_event('file_read_error', {
                'path': file_path, 'error': str(e)
            })
            return {'error': f'Error reading file: {e}'}
    
    def list_files(self, directory_path: str = ".", 
                   show_hidden: bool = False,
                   recursive: bool = False,
                   pattern: Optional[str] = None,
                   file_types: Optional[List[str]] = None) -> Dict:
        """List files in directory with filtering options"""
        try:
            path = Path(directory_path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(path), 'list'):
                self.security.log_security_event('directory_list_denied', {'path': str(path)})
                return {'error': 'Directory access denied for security reasons'}
            
            if not path.exists():
                return {'error': f'Directory not found: {directory_path}'}
                
            if not path.is_dir():
                return {'error': f'Path is not a directory: {directory_path}'}
            
            files = []
            
            # Get file iterator
            if recursive:
                iterator = path.rglob('*')
            else:
                iterator = path.iterdir()
            
            # Process files
            for file_path in iterator:
                try:
                    # Skip hidden files unless requested
                    if not show_hidden and file_path.name.startswith('.'):
                        continue
                    
                    # Apply pattern filtering
                    if pattern and not match_patterns(file_path.name, [pattern]):
                        continue
                    
                    # Apply file type filtering
                    if file_types:
                        if file_path.is_file():
                            ext = file_path.suffix.lower()
                            if ext not in file_types:
                                continue
                    
                    # Get file info
                    stat = file_path.stat()
                    file_info = FileInfo(
                        path=str(file_path),
                        name=file_path.name,
                        size=stat.st_size,
                        size_formatted=format_file_size(stat.st_size),
                        is_directory=file_path.is_dir(),
                        is_binary=is_binary_file(file_path) if file_path.is_file() else False,
                        modified_time=stat.st_mtime,
                        permissions=oct(stat.st_mode)[-3:]
                    )
                    
                    files.append(file_info)
                    
                except (PermissionError, OSError):
                    continue  # Skip files we can't access
            
            # Sort files (directories first, then alphabetically)
            files.sort(key=lambda x: (not x.is_directory, x.name.lower()))
            
            return {
                'success': True,
                'files': files,
                'total_count': len(files),
                'directory': str(path)
            }
            
        except Exception as e:
            self.security.log_security_event('directory_list_error', {
                'path': directory_path, 'error': str(e)
            })
            return {'error': f'Error listing directory: {e}'}
    
    def find_files(self, search_pattern: str,
                   search_path: str = ".",
                   case_sensitive: bool = False,
                   file_types: Optional[List[str]] = None,
                   max_results: int = MAX_FIND_RESULTS) -> Dict:
        """Find files matching pattern"""
        try:
            path = Path(search_path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(path), 'search'):
                self.security.log_security_event('file_search_denied', {'path': str(path)})
                return {'error': 'File search denied for security reasons'}
            
            if not path.exists():
                return {'error': f'Search path not found: {search_path}'}
            
            matches = []
            count = 0
            
            # Create search iterator
            iterator = path.rglob('*') if path.is_dir() else [path]
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(search_pattern, flags)
            except re.error as e:
                return {'error': f'Invalid regex pattern: {e}'}
            
            # Search files
            for file_path in iterator:
                if count >= max_results:
                    break
                
                try:
                    # Skip directories unless specifically searching for them
                    if file_path.is_dir():
                        continue
                    
                    # Apply file type filtering
                    if file_types:
                        ext = file_path.suffix.lower()
                        if ext not in file_types:
                            continue
                    
                    # Check if filename matches pattern
                    if pattern.search(file_path.name):
                        stat = file_path.stat()
                        matches.append({
                            'path': str(file_path),
                            'name': file_path.name,
                            'size': format_file_size(stat.st_size),
                            'modified': stat.st_mtime,
                            'match_type': 'filename'
                        })
                        count += 1
                
                except (PermissionError, OSError):
                    continue  # Skip files we can't access
            
            return {
                'success': True,
                'matches': matches,
                'total_found': len(matches),
                'search_pattern': search_pattern,
                'search_path': str(path),
                'truncated': count >= max_results
            }
            
        except Exception as e:
            self.security.log_security_event('file_search_error', {
                'pattern': search_pattern, 'path': search_path, 'error': str(e)
            })
            return {'error': f'Error searching files: {e}'}
    
    def grep_files(self, search_pattern: str,
                   search_path: str = ".",
                   case_sensitive: bool = False,
                   context_lines: int = 0,
                   file_types: Optional[List[str]] = None,
                   max_results: int = MAX_FIND_RESULTS) -> Dict:
        """Search for pattern within file contents"""
        try:
            path = Path(search_path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(path), 'grep'):
                self.security.log_security_event('grep_denied', {'path': str(path)})
                return {'error': 'Content search denied for security reasons'}
            
            if not path.exists():
                return {'error': f'Search path not found: {search_path}'}
            
            results = []
            files_searched = 0
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(search_pattern, flags)
            except re.error as e:
                return {'error': f'Invalid regex pattern: {e}'}
            
            # Create file iterator
            if path.is_file():
                files_to_search = [path]
            else:
                files_to_search = [f for f in path.rglob('*') if f.is_file()]
            
            # Search in files
            for file_path in files_to_search:
                if len(results) >= max_results:
                    break
                
                try:
                    # Apply file type filtering
                    if file_types:
                        ext = file_path.suffix.lower()
                        if ext not in file_types:
                            continue
                    
                    # Skip binary files
                    if is_binary_file(file_path):
                        continue
                    
                    # Read and search file content
                    content, encoding = safe_file_read(file_path)
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        match = pattern.search(line)
                        if match:
                            # Get context lines
                            context_before = []
                            context_after = []
                            
                            if context_lines > 0:
                                start_ctx = max(0, line_num - context_lines - 1)
                                end_ctx = min(len(lines), line_num + context_lines)
                                
                                context_before = lines[start_ctx:line_num-1]
                                context_after = lines[line_num:end_ctx]
                            
                            result = SearchResult(
                                file_path=str(file_path),
                                line_number=line_num,
                                line_content=line,
                                match_start=match.start(),
                                match_end=match.end(),
                                context_before=context_before,
                                context_after=context_after
                            )
                            
                            results.append(result)
                            
                            if len(results) >= max_results:
                                break
                    
                    files_searched += 1
                    
                except Exception:
                    continue  # Skip files we can't read
            
            return {
                'success': True,
                'results': results,
                'total_matches': len(results),
                'files_searched': files_searched,
                'search_pattern': search_pattern,
                'search_path': str(path),
                'truncated': len(results) >= max_results
            }
            
        except Exception as e:
            self.security.log_security_event('grep_error', {
                'pattern': search_pattern, 'path': search_path, 'error': str(e)
            })
            return {'error': f'Error searching file contents: {e}'}
```

### Phase 2: Integration with Tools Framework

#### Update `grok/tools.py`
```python
# Add file operations tools to TOOLS list
from .file_operations import FileOperations
from .security import SecurityManager

# Initialize file operations
security_manager = SecurityManager()
file_ops = FileOperations(security_manager)

# Add new tools to TOOLS list
TOOLS.extend([
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file content with optional line numbers and range selection",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"},
                    "show_line_numbers": {"type": "boolean", "description": "Show line numbers"},
                    "start_line": {"type": "integer", "description": "Starting line number"},
                    "max_lines": {"type": "integer", "description": "Maximum lines to read"}
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in directory with filtering options",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Directory path to list"},
                    "show_hidden": {"type": "boolean", "description": "Show hidden files"},
                    "recursive": {"type": "boolean", "description": "Recursive directory listing"},
                    "pattern": {"type": "string", "description": "File name pattern to match"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to filter"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Find files matching pattern in filename",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {"type": "string", "description": "Pattern to search for"},
                    "search_path": {"type": "string", "description": "Path to search in"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"},
                    "max_results": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["search_pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search for pattern within file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {"type": "string", "description": "Pattern to search for"},
                    "search_path": {"type": "string", "description": "Path to search in"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search"},
                    "context_lines": {"type": "integer", "description": "Number of context lines"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"},
                    "max_results": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["search_pattern"],
            },
        },
    }
])

# Add tool handlers
def handle_tool_call(tool_call, mode, permissions):
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    if func_name == "read_file":
        result = file_ops.read_file(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "list_files":
        result = file_ops.list_files(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "find_files":
        result = file_ops.find_files(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "grep_files":
        result = file_ops.grep_files(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    # Continue with existing tool handlers...
```

## Implementation Steps for Claude Code

### Step 1: Create Supporting Modules
```
Task: Create constants, utilities, and file operations modules

Instructions:
1. Create grok/constants.py with file operation constants and limits
2. Create grok/utils.py with utility functions for encoding detection, binary file detection, and safe file reading
3. Test utility functions by running basic file detection tests
4. Verify all constants are properly defined and accessible
```

### Step 2: Implement File Operations Framework
```
Task: Create comprehensive file operations module

Instructions:
1. Create grok/file_operations.py with FileOperations class
2. Implement read_file method with security integration
3. Implement list_files method with filtering capabilities
4. Implement find_files method with pattern matching
5. Implement grep_files method with content searching
6. Test each method individually to ensure proper functionality
```

### Step 3: Integrate with Tools Framework
```
Task: Integrate file operations with existing tools system

Instructions:
1. Update grok/tools.py to import file operations
2. Add new tool definitions to TOOLS list
3. Add tool handlers to handle_tool_call function
4. Test integration by calling each tool through the CLI
5. Verify security validation is working properly
```

### Step 4: Performance Optimization
```
Task: Optimize file operations for performance

Instructions:
1. Add caching for frequently accessed files
2. Implement lazy loading for large directories
3. Add progress indicators for long-running operations
4. Optimize regex compilation and reuse
5. Test performance with large directories and files
```

## Testing Strategy

### Unit Tests
- Individual file operation functions
- Security validation integration
- Error handling for edge cases
- Performance benchmarks

### Integration Tests
- Tool integration with CLI
- Security framework integration
- Cross-platform compatibility

### Performance Tests
- Large file handling
- Directory traversal performance
- Memory usage optimization

## Success Metrics
- All file operations work securely
- Performance meets requirements
- Comprehensive error handling
- Integration with security framework
- Cross-platform compatibility

## Next Steps
After completion of this task:
1. Task 004 (Development Tools) can build on file operations
2. Enhanced development workflows become possible
3. Foundation for advanced features is established