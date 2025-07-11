# Architecture: Task 005 - Implement Network and System Tools

## Overview
This task implements network and system operation tools that provide HTTP request capabilities, system information gathering, process management, and environment variable handling. These tools integrate with the security framework to ensure safe system operations.

## Technical Scope

### Files to Modify
- `grok/tools.py` - Add new network and system tools
- `grok/network_tools.py` - New network operations module
- `grok/system_tools.py` - New system operations module

### Dependencies
- Task 001 (Import Fixes) - Required for stable imports
- Task 002 (Security Framework) - Required for secure operations
- Task 003 (File Operations) - Required for file-based operations
- Task 004 (Development Tools) - Required for tool integration patterns

## Implementation Details

### Phase 1: Network Tools Module

#### Create `grok/network_tools.py`
```python
"""
Network operations tools for Grok CLI
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from .security import SecurityManager

class NetworkTools:
    """Network operations toolkit"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Grok-CLI/1.0'
        })
    
    def http_request(self, url: str, method: str = 'GET', 
                    headers: Optional[Dict[str, str]] = None,
                    data: Optional[Dict[str, Any]] = None,
                    timeout: int = 30) -> Dict:
        """Make HTTP request with security controls"""
        try:
            # Security validation
            if not self.security.validate_command(f'http_request {method} {url}'):
                return {'error': 'HTTP request denied for security reasons'}
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {'error': 'Invalid URL provided'}
            
            # Rate limiting
            if not self.security.rate_limiter.check_rate_limit('http_requests', 'api_calls'):
                return {'error': 'Rate limit exceeded for HTTP requests'}
            
            # Prepare request
            request_headers = headers or {}
            request_data = data or {}
            
            # Execute request
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                json=request_data if request_data else None,
                timeout=timeout
            )
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'url': response.url,
                'elapsed_time': response.elapsed.total_seconds()
            }
            
        except requests.exceptions.RequestException as e:
            return {'error': f'HTTP request failed: {e}'}
        except Exception as e:
            return {'error': f'Unexpected error: {e}'}
```

### Phase 2: System Tools Module

#### Create `grok/system_tools.py`
```python
"""
System operations tools for Grok CLI
"""

import os
import platform
import psutil
import subprocess
from typing import Dict, List, Optional
from .security import SecurityManager

class SystemTools:
    """System operations toolkit"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
    
    def system_info(self) -> Dict:
        """Get comprehensive system information"""
        try:
            return {
                'success': True,
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version()
                },
                'hardware': {
                    'cpu_count': psutil.cpu_count(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_total': psutil.virtual_memory().total,
                    'memory_available': psutil.virtual_memory().available,
                    'disk_usage': self._get_disk_usage()
                },
                'network': {
                    'interfaces': self._get_network_interfaces()
                },
                'environment': {
                    'user': os.getenv('USER', 'unknown'),
                    'home': os.getenv('HOME', 'unknown'),
                    'path': os.getenv('PATH', '').split(os.pathsep)[:5]  # First 5 paths
                }
            }
        except Exception as e:
            return {'error': f'Error getting system info: {e}'}
    
    def process_management(self, operation: str, **kwargs) -> Dict:
        """Process management operations"""
        try:
            # Security validation
            if not self.security.validate_command(f'process {operation}'):
                return {'error': 'Process operation denied for security reasons'}
            
            if operation == 'list':
                return self._list_processes(kwargs.get('filter', ''))
            elif operation == 'info':
                return self._get_process_info(kwargs.get('pid'))
            elif operation == 'kill':
                return self._kill_process(kwargs.get('pid'))
            else:
                return {'error': f'Unsupported process operation: {operation}'}
                
        except Exception as e:
            return {'error': f'Process operation failed: {e}'}
    
    def environment_variables(self, operation: str, **kwargs) -> Dict:
        """Environment variable management"""
        try:
            # Security validation
            if not self.security.validate_command(f'env {operation}'):
                return {'error': 'Environment operation denied for security reasons'}
            
            if operation == 'list':
                return self._list_env_vars(kwargs.get('filter', ''))
            elif operation == 'get':
                return self._get_env_var(kwargs.get('name'))
            elif operation == 'set':
                return self._set_env_var(kwargs.get('name'), kwargs.get('value'))
            else:
                return {'error': f'Unsupported environment operation: {operation}'}
                
        except Exception as e:
            return {'error': f'Environment operation failed: {e}'}
    
    def _get_disk_usage(self) -> Dict:
        """Get disk usage information"""
        try:
            usage = psutil.disk_usage('/')
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100
            }
        except Exception:
            return {'error': 'Could not get disk usage'}
    
    def _get_network_interfaces(self) -> List[Dict]:
        """Get network interface information"""
        try:
            interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {'name': interface, 'addresses': []}
                for addr in addrs:
                    interface_info['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
                interfaces.append(interface_info)
            return interfaces
        except Exception:
            return []
    
    def _list_processes(self, filter_str: str) -> Dict:
        """List running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if not filter_str or filter_str.lower() in proc_info['name'].lower():
                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'success': True,
                'processes': processes[:50],  # Limit to 50 processes
                'total_found': len(processes)
            }
        except Exception as e:
            return {'error': f'Error listing processes: {e}'}
    
    def _get_process_info(self, pid: int) -> Dict:
        """Get detailed process information"""
        try:
            proc = psutil.Process(pid)
            return {
                'success': True,
                'process': {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'cpu_percent': proc.cpu_percent(),
                    'memory_percent': proc.memory_percent(),
                    'create_time': proc.create_time(),
                    'cmdline': proc.cmdline()
                }
            }
        except psutil.NoSuchProcess:
            return {'error': f'Process with PID {pid} not found'}
        except psutil.AccessDenied:
            return {'error': f'Access denied to process {pid}'}
        except Exception as e:
            return {'error': f'Error getting process info: {e}'}
    
    def _kill_process(self, pid: int) -> Dict:
        """Kill a process (with safety checks)"""
        try:
            # Additional security check for killing processes
            if not self.security.validate_command(f'kill {pid}'):
                return {'error': 'Process termination denied for security reasons'}
            
            proc = psutil.Process(pid)
            proc.terminate()
            
            return {
                'success': True,
                'message': f'Process {pid} terminated'
            }
        except psutil.NoSuchProcess:
            return {'error': f'Process with PID {pid} not found'}
        except psutil.AccessDenied:
            return {'error': f'Access denied to terminate process {pid}'}
        except Exception as e:
            return {'error': f'Error terminating process: {e}'}
    
    def _list_env_vars(self, filter_str: str) -> Dict:
        """List environment variables"""
        try:
            # Filter sensitive environment variables
            sensitive_vars = {'API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'PRIVATE'}
            
            env_vars = {}
            for key, value in os.environ.items():
                if not filter_str or filter_str.lower() in key.lower():
                    # Hide sensitive values
                    if any(sensitive in key.upper() for sensitive in sensitive_vars):
                        env_vars[key] = '***HIDDEN***'
                    else:
                        env_vars[key] = value
            
            return {
                'success': True,
                'environment_variables': env_vars,
                'total_count': len(env_vars)
            }
        except Exception as e:
            return {'error': f'Error listing environment variables: {e}'}
    
    def _get_env_var(self, name: str) -> Dict:
        """Get specific environment variable"""
        try:
            value = os.getenv(name)
            if value is None:
                return {'error': f'Environment variable {name} not found'}
            
            # Hide sensitive values
            sensitive_vars = {'API_KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'PRIVATE'}
            if any(sensitive in name.upper() for sensitive in sensitive_vars):
                value = '***HIDDEN***'
            
            return {
                'success': True,
                'name': name,
                'value': value
            }
        except Exception as e:
            return {'error': f'Error getting environment variable: {e}'}
    
    def _set_env_var(self, name: str, value: str) -> Dict:
        """Set environment variable (process scope only)"""
        try:
            # Security validation for setting environment variables
            if not self.security.validate_command(f'setenv {name}'):
                return {'error': 'Setting environment variable denied for security reasons'}
            
            os.environ[name] = value
            
            return {
                'success': True,
                'message': f'Environment variable {name} set (process scope only)'
            }
        except Exception as e:
            return {'error': f'Error setting environment variable: {e}'}
```

### Phase 3: Tool Integration

#### Update `grok/tools.py`
```python
# Add network and system tools
from .network_tools import NetworkTools
from .system_tools import SystemTools

# Initialize tools
network_tools = NetworkTools(security_manager)
system_tools = SystemTools(security_manager)

# Add new tools to TOOLS list
TOOLS.extend([
    {
        "type": "function",
        "function": {
            "name": "http_request",
            "description": "Make HTTP requests with authentication and error handling",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "data": {"type": "object", "description": "Request data"},
                    "timeout": {"type": "integer", "description": "Request timeout"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_info",
            "description": "Get comprehensive system information",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_management",
            "description": "Process management operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Operation: list, info, kill"},
                    "pid": {"type": "integer", "description": "Process ID"},
                    "filter": {"type": "string", "description": "Filter for process names"}
                },
                "required": ["operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "environment_variables",
            "description": "Environment variable management",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Operation: list, get, set"},
                    "name": {"type": "string", "description": "Variable name"},
                    "value": {"type": "string", "description": "Variable value"},
                    "filter": {"type": "string", "description": "Filter for variable names"}
                },
                "required": ["operation"],
            },
        },
    }
])

# Add tool handlers
def handle_tool_call(tool_call, mode, permissions):
    # ... existing handlers ...
    
    elif func_name == "http_request":
        result = network_tools.http_request(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "system_info":
        result = system_tools.system_info()
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "process_management":
        result = system_tools.process_management(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "environment_variables":
        result = system_tools.environment_variables(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
```

## Implementation Steps for Claude Code

### Step 1: Create Network Tools Module
```
Task: Create comprehensive network operations module

Instructions:
1. Create grok/network_tools.py with NetworkTools class
2. Implement http_request method with security validation
3. Add rate limiting and request validation
4. Implement proper error handling and response parsing
5. Test HTTP operations with various endpoints and methods
```

### Step 2: Create System Tools Module
```
Task: Create comprehensive system operations module

Instructions:
1. Create grok/system_tools.py with SystemTools class
2. Implement system_info method for comprehensive system data
3. Implement process_management for safe process operations
4. Implement environment_variables for secure env var handling
5. Add security controls for all system operations
6. Test system operations across different platforms
```

### Step 3: Integrate with Tools Framework
```
Task: Integrate network and system tools with existing tools system

Instructions:
1. Update grok/tools.py to import network and system tools
2. Add new tool definitions to TOOLS list
3. Add tool handlers to handle_tool_call function
4. Test integration through CLI interface
5. Verify security validation for all operations
```

### Step 4: Add Dependencies
```
Task: Add required dependencies for network and system operations

Instructions:
1. Add requests library to requirements.txt
2. Add psutil library to requirements.txt
3. Update setup.py with new dependencies
4. Test installation with new dependencies
```

## Testing Strategy

### Unit Tests
- HTTP request functionality
- System information gathering
- Process management operations
- Environment variable handling
- Security validation integration

### Integration Tests
- Network connectivity testing
- Cross-platform system operations
- Performance under load
- Security enforcement

### Security Tests
- Rate limiting enforcement
- Command validation
- Process termination controls
- Environment variable protection

## Success Metrics
- Secure HTTP operations
- Comprehensive system information
- Safe process management
- Protected environment access
- Cross-platform compatibility

## Next Steps
After completion of this task:
1. Task 006 (Error Handling) can add comprehensive error management
2. Network-based integrations become possible
3. System monitoring capabilities are established