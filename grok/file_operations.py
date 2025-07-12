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