"""
Core security framework for Grok CLI
Provides input validation, command filtering, and security controls
"""

import re
import os
import hashlib
import logging
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from .config import load_settings


class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass


class SecurityManager:
    """Central security management class"""
    
    def __init__(self):
        self.settings = load_settings()
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
        self.input_validator = InputValidator()
        self.command_filter = CommandFilter()
        self.file_guardian = FileGuardian()
    
    def validate_input(self, user_input: str) -> str:
        """Validate and sanitize user input"""
        return self.input_validator.sanitize(user_input)
    
    def validate_command(self, command: str) -> bool:
        """Validate command execution request"""
        return self.command_filter.is_allowed(command)
    
    def validate_file_operation(self, path: str, operation: str) -> bool:
        """Validate file operation request"""
        return self.file_guardian.is_allowed(path, operation)
    
    def log_security_event(self, event_type: str, details: Dict):
        """Log security-related events"""
        self.audit_logger.log_event(event_type, details)


class RateLimiter:
    """Rate limiting for API calls and commands"""
    
    def __init__(self):
        self.requests = {}
        self.limits = {
            'api_calls': {'count': 100, 'window': 3600},  # 100 per hour
            'commands': {'count': 50, 'window': 300},     # 50 per 5 minutes
        }
    
    def check_rate_limit(self, key: str, limit_type: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        window = self.limits[limit_type]['window']
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.limits[limit_type]['count']:
            return False
        
        self.requests[key].append(current_time)
        return True


class InputValidator:
    """Input validation and sanitization"""
    
    def __init__(self):
        self.max_input_length = 10000
        self.dangerous_patterns = [
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',  # Control characters
            r'<script[^>]*>.*?</script>',                # Script tags
            r'javascript:',                              # JavaScript URLs
            r'data:text/html',                          # Data URLs
        ]
    
    def sanitize(self, user_input: str) -> str:
        """Sanitize user input"""
        if len(user_input) > self.max_input_length:
            raise SecurityError(f"Input exceeds maximum length of {self.max_input_length}")
        
        # Remove dangerous patterns
        sanitized = user_input
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized


class CommandFilter:
    """Command filtering and validation"""
    
    def __init__(self):
        self.dangerous_commands = {
            'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd',
            'sudo', 'su', 'chmod', 'chown', 'passwd',
            'curl', 'wget', 'nc', 'netcat', 'telnet',
            'eval', 'exec', 'python -c', 'perl -e',
        }
        
        self.dangerous_patterns = [
            r';\s*rm\s+',           # Command chaining with rm
            r'&&\s*rm\s+',          # Command chaining with rm
            r'\|\s*sh\s*',          # Pipe to shell
            r'`[^`]*`',             # Command substitution
            r'\$\([^)]*\)',         # Command substitution
            r'>\s*/dev/',           # Redirect to device files
            r'<\s*/dev/',           # Read from device files
        ]
    
    def is_allowed(self, command: str) -> bool:
        """Check if command is allowed"""
        # Check for dangerous commands
        cmd_parts = command.lower().split()
        if cmd_parts and cmd_parts[0] in self.dangerous_commands:
            return False
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        return True


class FileGuardian:
    """File system security controls"""
    
    def __init__(self):
        self.restricted_paths = {
            '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin',
            '/boot', '/dev', '/proc', '/sys', '/root',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32',
        }
        
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            '.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml',
            '.toml', '.ini', '.cfg', '.conf', '.log', '.csv',
        }
    
    def is_allowed(self, path: str, operation: str) -> bool:
        """Check if file operation is allowed"""
        try:
            # Resolve path to prevent directory traversal
            resolved_path = Path(path).resolve()
            
            # Check for restricted paths
            for restricted in self.restricted_paths:
                if str(resolved_path).startswith(restricted):
                    return False
            
            # Check file extension for certain operations
            if operation in ['read', 'write']:
                if resolved_path.suffix.lower() not in self.allowed_extensions:
                    return False
            
            # Check file size for write operations
            if operation == 'write' and resolved_path.exists():
                if resolved_path.stat().st_size > self.max_file_size:
                    return False
            
            return True
            
        except Exception:
            return False


class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger('grok.security')
        self.logger.setLevel(logging.INFO)
        
        # Create secure log file
        log_dir = Path.home() / '.grok' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_dir / 'security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, details: Dict):
        """Log security event"""
        self.logger.info(f"Security Event: {event_type} - {details}")