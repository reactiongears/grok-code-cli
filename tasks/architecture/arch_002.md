# Architecture: Task 002 - Implement Comprehensive Security Framework

## Overview
This task establishes a robust security foundation for the Grok CLI, addressing critical vulnerabilities in command execution, file operations, and API handling. The security framework will be integrated throughout the system architecture.

## Technical Scope

### Files to Modify
- `grok/security.py` - New security framework module
- `grok/tools.py` - Integrate security controls
- `grok/agent.py` - Add security validation
- `grok/config.py` - Secure configuration handling
- `grok/validators.py` - New input validation module

### Dependencies
- Task 001 (Critical Import Fixes) - Required for stable foundation

## Architectural Approach

### 1. Layered Security Architecture
```
Application Layer     (User Interface)
    ↓
Validation Layer     (Input Sanitization)
    ↓
Authorization Layer  (Permission Controls)
    ↓
Execution Layer      (Secure Command/File Operations)
    ↓
Audit Layer         (Security Logging)
```

### 2. Security Components

#### A. Input Validation Framework
- Sanitize all user inputs
- Validate command parameters
- Prevent injection attacks

#### B. Command Security System
- Whitelist/blacklist validation
- Command pattern matching
- Dangerous command detection

#### C. File System Security
- Path traversal prevention
- Access control validation
- Secure file operations

#### D. API Security
- Secure key storage
- Rate limiting
- Request validation

#### E. Audit and Logging
- Security event tracking
- Attack pattern detection
- Compliance logging

## Implementation Details

### Phase 1: Security Framework Foundation

#### Create `grok/security.py`
```python
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
```

### Phase 2: Integration with Tools

#### Update `grok/tools.py`
```python
# Add security integration
from .security import SecurityManager

# Initialize security manager
security_manager = SecurityManager()

def handle_tool_call(tool_call, mode, permissions):
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    # Security validation
    if func_name == "edit_file":
        path = args['path']
        content = args['content']
        
        # Validate file operation
        if not security_manager.validate_file_operation(path, 'write'):
            security_manager.log_security_event('file_access_denied', {
                'path': path, 'operation': 'write'
            })
            return {"tool_call_id": tool_call.id, "output": "File access denied for security reasons."}
        
        # Sanitize content
        try:
            sanitized_content = security_manager.validate_input(content)
        except SecurityError as e:
            security_manager.log_security_event('input_validation_failed', {
                'error': str(e)
            })
            return {"tool_call_id": tool_call.id, "output": f"Input validation failed: {e}"}
        
        # Continue with original logic using sanitized_content
        
    elif func_name == "run_bash":
        cmd = args['cmd']
        
        # Validate command
        if not security_manager.validate_command(cmd):
            security_manager.log_security_event('command_blocked', {
                'command': cmd, 'reason': 'dangerous_command'
            })
            return {"tool_call_id": tool_call.id, "output": "Command blocked for security reasons."}
        
        # Continue with original logic
```

### Phase 3: API Security Enhancement

#### Update `grok/agent.py`
```python
from .security import SecurityManager

# Initialize security manager
security_manager = SecurityManager()

def call_api(messages, tools=None, api_key=None):
    # Rate limiting check
    if not security_manager.rate_limiter.check_rate_limit('api_calls', 'api_calls'):
        raise SecurityError("API rate limit exceeded")
    
    # Validate API key
    if api_key is None:
        api_key = load_settings().get('api_key')
    
    if not api_key:
        raise SecurityError("No API key provided")
    
    # Continue with API call logic
```

## Implementation Steps for Claude Code

### Step 1: Create Security Framework
```
Task: Create comprehensive security framework module

Instructions:
1. Create new file grok/security.py
2. Implement SecurityManager class with all security components
3. Add RateLimiter class for API and command rate limiting
4. Implement InputValidator class for input sanitization
5. Create CommandFilter class for command validation
6. Add FileGuardian class for file system security
7. Implement AuditLogger class for security event logging
8. Test security framework by importing and creating SecurityManager instance
```

### Step 2: Integrate Security into Tools
```
Task: Integrate security controls into tools.py

Instructions:
1. Import SecurityManager from security module
2. Initialize security_manager instance at module level
3. Add security validation to edit_file function
4. Add security validation to run_bash function
5. Implement security event logging for blocked operations
6. Test tool security by attempting blocked operations
```

### Step 3: Add API Security
```
Task: Enhance API security in agent.py

Instructions:
1. Import SecurityManager and SecurityError
2. Initialize security_manager instance
3. Add rate limiting to call_api function
4. Add API key validation
5. Implement security logging for API operations
6. Test API security by making rapid API calls to test rate limiting
```

### Step 4: Configuration Security
```
Task: Secure configuration handling

Instructions:
1. Add secure storage for API keys
2. Implement configuration validation
3. Add encryption for sensitive settings
4. Create secure configuration file permissions
5. Test configuration security by validating stored credentials
```

## Testing Strategy

### Security Testing
- Input validation tests with malicious inputs
- Command injection prevention tests
- File system access control tests
- API rate limiting tests
- Audit logging verification

### Integration Testing
- Security integration with existing tools
- Performance impact assessment
- Error handling validation

## Risk Mitigation

### Performance Considerations
- Efficient security checks to minimize latency
- Caching for validation results
- Asynchronous audit logging

### Usability Balance
- Clear security error messages
- Reasonable default security settings
- Override mechanisms for power users

## Success Metrics
- Zero security vulnerabilities in penetration testing
- All dangerous commands blocked
- File system access properly restricted
- API rate limiting functional
- Comprehensive audit trail maintained

## Next Steps
After completion of this task:
1. Task 003 (File Operations) can safely implement secure file handling
2. All subsequent tasks will inherit security controls
3. Security framework can be extended for additional protections