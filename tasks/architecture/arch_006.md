# Architecture: Task 006 - Implement Error Handling and Logging Framework

## Overview
This task creates a comprehensive error handling and logging framework that provides centralized error management, structured logging, user-friendly error messages, and retry mechanisms for transient failures.

## Technical Scope

### Files to Modify
- `grok/error_handling.py` - New error handling framework
- `grok/logging_config.py` - New logging configuration
- All existing modules - Integrate error handling

### Dependencies
- Task 001-005 (Foundation) - Required for stable base

## Implementation Details

### Phase 1: Error Handling Framework

#### Create `grok/error_handling.py`
```python
"""
Comprehensive error handling framework for Grok CLI
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from functools import wraps

class ErrorLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    SECURITY = "security"
    API = "api"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    CONFIGURATION = "configuration"

@dataclass
class ErrorInfo:
    """Error information structure"""
    error_id: str
    level: ErrorLevel
    category: ErrorCategory
    message: str
    technical_details: str
    user_message: str
    suggestions: List[str]
    timestamp: float
    context: Dict[str, Any]

class ErrorHandler:
    """Central error handling system"""
    
    def __init__(self):
        self.logger = logging.getLogger('grok.errors')
        self.error_templates = self._initialize_error_templates()
        self.retry_strategies = self._initialize_retry_strategies()
    
    def _initialize_error_templates(self) -> Dict[str, Dict]:
        """Initialize error message templates"""
        return {
            'file_not_found': {
                'user_message': 'File not found: {file_path}',
                'suggestions': [
                    'Check if the file path is correct',
                    'Verify file permissions',
                    'Use list_files to see available files'
                ]
            },
            'permission_denied': {
                'user_message': 'Permission denied for {operation}',
                'suggestions': [
                    'Check file/directory permissions',
                    'Try running with appropriate privileges',
                    'Contact administrator if needed'
                ]
            },
            'network_error': {
                'user_message': 'Network connection failed',
                'suggestions': [
                    'Check internet connectivity',
                    'Verify the URL is correct',
                    'Try again in a few moments'
                ]
            },
            'api_error': {
                'user_message': 'API request failed: {status_code}',
                'suggestions': [
                    'Check API key validity',
                    'Verify API endpoint',
                    'Review rate limits'
                ]
            },
            'security_violation': {
                'user_message': 'Security policy violation',
                'suggestions': [
                    'Review security settings',
                    'Contact administrator',
                    'Check command permissions'
                ]
            }
        }
    
    def _initialize_retry_strategies(self) -> Dict[str, Dict]:
        """Initialize retry strategies for different error types"""
        return {
            'network': {
                'max_retries': 3,
                'base_delay': 1,
                'max_delay': 10,
                'backoff_factor': 2
            },
            'api': {
                'max_retries': 5,
                'base_delay': 1,
                'max_delay': 30,
                'backoff_factor': 1.5
            },
            'file_system': {
                'max_retries': 2,
                'base_delay': 0.5,
                'max_delay': 2,
                'backoff_factor': 2
            }
        }
    
    def handle_error(self, error: Exception, category: ErrorCategory, 
                    context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle and process error with context"""
        error_id = f"{category.value}_{int(time.time())}"
        context = context or {}
        
        # Determine error level
        level = self._determine_error_level(error, category)
        
        # Generate user-friendly message
        user_message, suggestions = self._generate_user_message(error, category, context)
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            level=level,
            category=category,
            message=str(error),
            technical_details=traceback.format_exc(),
            user_message=user_message,
            suggestions=suggestions,
            timestamp=time.time(),
            context=context
        )
        
        # Log error
        self._log_error(error_info)
        
        return error_info
    
    def _determine_error_level(self, error: Exception, category: ErrorCategory) -> ErrorLevel:
        """Determine appropriate error level"""
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return ErrorLevel.WARNING
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorLevel.ERROR
        elif category == ErrorCategory.SECURITY:
            return ErrorLevel.CRITICAL
        else:
            return ErrorLevel.ERROR
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory, 
                              context: Dict[str, Any]) -> tuple[str, List[str]]:
        """Generate user-friendly error message"""
        error_type = type(error).__name__.lower()
        
        # Try to find specific template
        template = None
        if 'file' in error_type and 'not' in str(error).lower():
            template = self.error_templates.get('file_not_found')
        elif 'permission' in error_type:
            template = self.error_templates.get('permission_denied')
        elif category == ErrorCategory.NETWORK:
            template = self.error_templates.get('network_error')
        elif category == ErrorCategory.API:
            template = self.error_templates.get('api_error')
        elif category == ErrorCategory.SECURITY:
            template = self.error_templates.get('security_violation')
        
        if template:
            try:
                user_message = template['user_message'].format(**context)
                suggestions = template['suggestions']
            except KeyError:
                user_message = str(error)
                suggestions = template['suggestions']
        else:
            user_message = str(error)
            suggestions = ['Try the operation again', 'Check the logs for more details']
        
        return user_message, suggestions
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error information"""
        log_data = {
            'error_id': error_info.error_id,
            'level': error_info.level.value,
            'category': error_info.category.value,
            'message': error_info.message,
            'context': error_info.context
        }
        
        if error_info.level == ErrorLevel.CRITICAL:
            self.logger.critical(f"Critical error: {log_data}")
        elif error_info.level == ErrorLevel.ERROR:
            self.logger.error(f"Error: {log_data}")
        elif error_info.level == ErrorLevel.WARNING:
            self.logger.warning(f"Warning: {log_data}")
        else:
            self.logger.info(f"Info: {log_data}")

class RetryManager:
    """Retry mechanism for transient failures"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
    
    def retry_with_backoff(self, func: Callable, category: str, 
                          max_retries: Optional[int] = None,
                          context: Dict[str, Any] = None) -> Any:
        """Retry function with exponential backoff"""
        strategy = self.error_handler.retry_strategies.get(category, {})
        max_retries = max_retries or strategy.get('max_retries', 3)
        base_delay = strategy.get('base_delay', 1)
        max_delay = strategy.get('max_delay', 10)
        backoff_factor = strategy.get('backoff_factor', 2)
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                last_error = e
                
                if attempt == max_retries:
                    # Final attempt failed
                    error_info = self.error_handler.handle_error(
                        e, ErrorCategory(category), context
                    )
                    raise e
                
                # Calculate delay for next attempt
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                time.sleep(delay)
                
                # Log retry attempt
                self.error_handler.logger.info(
                    f"Retry attempt {attempt + 1} for {func.__name__} after {delay}s"
                )
        
        # This should not be reached
        raise last_error

def error_handler(category: ErrorCategory, context: Dict[str, Any] = None):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                error_info = handler.handle_error(e, category, context)
                # Return error info instead of raising
                return {'error': error_info.user_message, 'error_id': error_info.error_id}
        return wrapper
    return decorator

def retryable(category: str, max_retries: int = 3):
    """Decorator for retryable functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler()
            retry_manager = RetryManager(handler)
            return retry_manager.retry_with_backoff(
                lambda: func(*args, **kwargs),
                category,
                max_retries
            )
        return wrapper
    return decorator
```

### Phase 2: Logging Configuration

#### Create `grok/logging_config.py`
```python
"""
Logging configuration for Grok CLI
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any

class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir) if log_dir else Path.home() / '.grok' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self, level: str = 'INFO') -> None:
        """Setup comprehensive logging configuration"""
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'grok.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Security log handler
        security_logger = logging.getLogger('grok.security')
        security_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'security.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(detailed_formatter)
        security_logger.addHandler(security_handler)
        
        # Performance log handler
        perf_logger = logging.getLogger('grok.performance')
        perf_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'performance.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        perf_logger.addHandler(perf_handler)
```

### Phase 3: Integration with Existing Modules

#### Update existing modules to use error handling
```python
# Example integration in existing modules
from .error_handling import ErrorHandler, ErrorCategory, error_handler, retryable

class ExampleModule:
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    @error_handler(ErrorCategory.FILE_SYSTEM)
    def read_file(self, file_path: str):
        # File reading logic
        pass
    
    @retryable('network', max_retries=3)
    def api_call(self, url: str):
        # API call logic
        pass
```

## Implementation Steps for Claude Code

### Step 1: Create Error Handling Framework
```
Task: Create comprehensive error handling system

Instructions:
1. Create grok/error_handling.py with ErrorHandler class
2. Implement error classification and message templates
3. Create retry mechanism with exponential backoff
4. Add error decorators for automatic handling
5. Test error handling with various error scenarios
```

### Step 2: Create Logging Configuration
```
Task: Setup comprehensive logging system

Instructions:
1. Create grok/logging_config.py with LoggingConfig class
2. Configure multiple log handlers (console, file, error, security)
3. Set up log rotation and retention policies
4. Create separate loggers for different components
5. Test logging configuration and log file generation
```

### Step 3: Integrate with Existing Modules
```
Task: Integrate error handling throughout the codebase

Instructions:
1. Update all existing modules to use error handling
2. Add error decorators to critical functions
3. Replace ad-hoc error handling with centralized system
4. Update tool handlers to use error framework
5. Test integration across all modules
```

## Testing Strategy

### Unit Tests
- Error classification accuracy
- Message template generation
- Retry mechanism behavior
- Logging configuration

### Integration Tests
- Error handling across modules
- Log file generation and rotation
- Performance impact assessment

## Success Metrics
- Centralized error handling
- User-friendly error messages
- Comprehensive logging
- Reliable retry mechanisms
- Performance optimization

## Next Steps
After completion of this task:
1. All subsequent tasks benefit from robust error handling
2. Debugging and troubleshooting become easier
3. User experience is significantly improved