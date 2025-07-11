# Architecture: Task 014 - Implement External Dependencies Health Check System

## Overview
This task implements a comprehensive health check system that monitors and validates external dependencies including xAI API, VS Code, system tools, and network connectivity to ensure reliable operation and graceful degradation.

## Technical Scope

### Files to Modify
- `grok/health_check/` - New health check system package
- `grok/dependency_monitor/` - New dependency monitoring system
- `grok/graceful_degradation/` - New graceful degradation handlers
- `grok/startup_validator.py` - New startup validation system

### Dependencies
- Task 013 (Monitoring System) - Required for health check metrics
- Task 006 (Error Handling) - Required for health check error management
- Task 005 (Network Tools) - Required for connectivity testing

## Implementation Details

### Phase 1: Core Health Check Framework

#### Create `grok/health_check/core.py`
```python
"""
Core health check framework for Grok CLI
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import subprocess
import requests
import json
from pathlib import Path

from ..error_handling import ErrorHandler, ErrorCategory
from ..config import ConfigManager

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float
    check_duration: float
    
    def is_healthy(self) -> bool:
        """Check if status is healthy"""
        return self.status == HealthStatus.HEALTHY
    
    def is_degraded(self) -> bool:
        """Check if status is degraded"""
        return self.status == HealthStatus.DEGRADED

class BaseHealthCheck:
    """Base health check class"""
    
    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
        self.last_result: Optional[HealthCheckResult] = None
        self.check_count = 0
        self.failure_count = 0
    
    async def check(self) -> HealthCheckResult:
        """Perform health check"""
        start_time = time.time()
        
        try:
            self.check_count += 1
            result = await asyncio.wait_for(
                self._perform_check(), 
                timeout=self.timeout
            )
            
            if not result.is_healthy():
                self.failure_count += 1
            
            result.timestamp = time.time()
            result.check_duration = result.timestamp - start_time
            self.last_result = result
            
            return result
            
        except asyncio.TimeoutError:
            self.failure_count += 1
            result = HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                details={},
                timestamp=time.time(),
                check_duration=self.timeout
            )
            self.last_result = result
            return result
            
        except Exception as e:
            self.failure_count += 1
            result = HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=time.time(),
                check_duration=time.time() - start_time
            )
            self.last_result = result
            return result
    
    async def _perform_check(self) -> HealthCheckResult:
        """Override this method to implement specific health check logic"""
        raise NotImplementedError
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        if self.check_count == 0:
            return 0.0
        return self.failure_count / self.check_count

class HealthCheckManager:
    """Manager for all health checks"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.error_handler = ErrorHandler()
        self.health_checks: Dict[str, BaseHealthCheck] = {}
        self.check_results: Dict[str, HealthCheckResult] = {}
        self.running = False
        self.check_interval = 60  # seconds
        
        # Load configuration
        self.config = config_manager.load_settings()
        self.health_config = self.config.get('health_checks', {})
        
        # Initialize health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check(APIHealthCheck())
        self.register_check(VSCodeHealthCheck())
        self.register_check(SystemToolsHealthCheck())
        self.register_check(NetworkConnectivityCheck())
        self.register_check(DiskSpaceCheck())
        self.register_check(MemoryHealthCheck())
    
    def register_check(self, health_check: BaseHealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
    
    def unregister_check(self, name: str):
        """Unregister a health check"""
        if name in self.health_checks:
            del self.health_checks[name]
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        # Run checks concurrently
        tasks = []
        for name, health_check in self.health_checks.items():
            task = asyncio.create_task(health_check.check())
            tasks.append((name, task))
        
        # Wait for all checks to complete
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
                self.check_results[name] = result
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, {"health_check": name}
                )
        
        return results
    
    async def check_single(self, name: str) -> Optional[HealthCheckResult]:
        """Run a single health check"""
        if name not in self.health_checks:
            return None
        
        try:
            result = await self.health_checks[name].check()
            self.check_results[name] = result
            return result
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"health_check": name}
            )
            return None
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        if not self.check_results:
            return {
                "overall_status": HealthStatus.UNKNOWN,
                "message": "No health checks performed yet",
                "checks": {}
            }
        
        # Calculate overall status
        healthy_count = sum(1 for r in self.check_results.values() if r.is_healthy())
        degraded_count = sum(1 for r in self.check_results.values() if r.is_degraded())
        total_checks = len(self.check_results)
        
        if healthy_count == total_checks:
            overall_status = HealthStatus.HEALTHY
            message = "All systems operational"
        elif degraded_count > 0 and healthy_count + degraded_count == total_checks:
            overall_status = HealthStatus.DEGRADED
            message = "Some systems degraded but operational"
        else:
            overall_status = HealthStatus.UNHEALTHY
            message = "Critical systems unavailable"
        
        return {
            "overall_status": overall_status,
            "message": message,
            "checks": {name: result for name, result in self.check_results.items()},
            "summary": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": total_checks - healthy_count - degraded_count,
                "total": total_checks
            }
        }
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self.running = True
        
        while self.running:
            try:
                await self.check_all()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, {"operation": "health_monitoring"}
                )
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.running = False
```

#### Create `grok/health_check/checks.py`
```python
"""
Specific health check implementations
"""

import subprocess
import requests
import psutil
import shutil
from pathlib import Path
import json
import socket

from .core import BaseHealthCheck, HealthStatus, HealthCheckResult

class APIHealthCheck(BaseHealthCheck):
    """Health check for xAI API connectivity"""
    
    def __init__(self):
        super().__init__("xai_api", timeout=10)
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check API connectivity and authentication"""
        try:
            # Get API key from environment or config
            api_key = os.getenv('XAI_API_KEY') or self.config.get('api_key')
            
            if not api_key:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="API key not configured",
                    details={"error": "Missing API key"}
                )
            
            # Test API connectivity
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Simple API test call
            response = requests.get(
                'https://api.x.ai/v1/models',
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                models = response.json()
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="API connectivity verified",
                    details={
                        "models_count": len(models.get('data', [])),
                        "response_time": response.elapsed.total_seconds()
                    }
                )
            elif response.status_code == 401:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    message="API authentication failed",
                    details={"status_code": response.status_code}
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message=f"API returned status {response.status_code}",
                    details={"status_code": response.status_code}
                )
        
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="API request timed out",
                details={"timeout": self.timeout}
            )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Cannot connect to API",
                details={"error": "Connection error"}
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"API check failed: {str(e)}",
                details={"error": str(e)}
            )

class VSCodeHealthCheck(BaseHealthCheck):
    """Health check for VS Code availability"""
    
    def __init__(self):
        super().__init__("vscode", timeout=5)
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check VS Code installation and functionality"""
        try:
            # Check if VS Code is installed
            result = subprocess.run(
                ['code', '--version'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                version_info = result.stdout.strip().split('\n')
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="VS Code is available",
                    details={
                        "version": version_info[0] if version_info else "unknown",
                        "commit": version_info[1] if len(version_info) > 1 else "unknown"
                    }
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message="VS Code command failed",
                    details={"stderr": result.stderr}
                )
        
        except subprocess.TimeoutExpired:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="VS Code check timed out",
                details={"timeout": self.timeout}
            )
        except FileNotFoundError:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="VS Code not found in PATH",
                details={"note": "Diff functionality will be limited"}
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"VS Code check failed: {str(e)}",
                details={"error": str(e)}
            )

class SystemToolsHealthCheck(BaseHealthCheck):
    """Health check for required system tools"""
    
    def __init__(self):
        super().__init__("system_tools", timeout=10)
        self.required_tools = ['git', 'python', 'pip']
        self.optional_tools = ['node', 'npm', 'docker', 'kubectl']
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check availability of system tools"""
        try:
            available_tools = {}
            missing_required = []
            missing_optional = []
            
            # Check required tools
            for tool in self.required_tools:
                try:
                    result = subprocess.run(
                        [tool, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        available_tools[tool] = result.stdout.strip().split('\n')[0]
                    else:
                        missing_required.append(tool)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    missing_required.append(tool)
            
            # Check optional tools
            for tool in self.optional_tools:
                try:
                    result = subprocess.run(
                        [tool, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        available_tools[tool] = result.stdout.strip().split('\n')[0]
                    else:
                        missing_optional.append(tool)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    missing_optional.append(tool)
            
            # Determine status
            if missing_required:
                status = HealthStatus.UNHEALTHY
                message = f"Missing required tools: {', '.join(missing_required)}"
            elif missing_optional:
                status = HealthStatus.DEGRADED
                message = f"Some optional tools missing: {', '.join(missing_optional)}"
            else:
                status = HealthStatus.HEALTHY
                message = "All system tools available"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "available_tools": available_tools,
                    "missing_required": missing_required,
                    "missing_optional": missing_optional
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"System tools check failed: {str(e)}",
                details={"error": str(e)}
            )

class NetworkConnectivityCheck(BaseHealthCheck):
    """Health check for network connectivity"""
    
    def __init__(self):
        super().__init__("network", timeout=10)
        self.test_hosts = [
            ('google.com', 80),
            ('github.com', 443),
            ('api.x.ai', 443)
        ]
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check network connectivity to key services"""
        try:
            connectivity_results = {}
            failed_hosts = []
            
            for host, port in self.test_hosts:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        connectivity_results[host] = "connected"
                    else:
                        connectivity_results[host] = "failed"
                        failed_hosts.append(host)
                        
                except Exception as e:
                    connectivity_results[host] = f"error: {str(e)}"
                    failed_hosts.append(host)
            
            # Determine status
            if not failed_hosts:
                status = HealthStatus.HEALTHY
                message = "Network connectivity verified"
            elif len(failed_hosts) < len(self.test_hosts):
                status = HealthStatus.DEGRADED
                message = f"Some hosts unreachable: {', '.join(failed_hosts)}"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Network connectivity issues detected"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "connectivity_results": connectivity_results,
                    "failed_hosts": failed_hosts
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Network check failed: {str(e)}",
                details={"error": str(e)}
            )

class DiskSpaceCheck(BaseHealthCheck):
    """Health check for disk space availability"""
    
    def __init__(self):
        super().__init__("disk_space", timeout=5)
        self.warning_threshold = 0.8  # 80% full
        self.critical_threshold = 0.95  # 95% full
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check disk space availability"""
        try:
            # Get disk usage for current directory
            usage = shutil.disk_usage(Path.cwd())
            
            total_bytes = usage.total
            free_bytes = usage.free
            used_bytes = usage.used
            
            used_percentage = used_bytes / total_bytes
            free_gb = free_bytes / (1024 ** 3)
            
            # Determine status
            if used_percentage >= self.critical_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.1f}GB free ({used_percentage:.1%} used)"
            elif used_percentage >= self.warning_threshold:
                status = HealthStatus.DEGRADED
                message = f"Warning: {free_gb:.1f}GB free ({used_percentage:.1%} used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient disk space: {free_gb:.1f}GB free"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "total_gb": total_bytes / (1024 ** 3),
                    "free_gb": free_gb,
                    "used_percentage": used_percentage,
                    "warning_threshold": self.warning_threshold,
                    "critical_threshold": self.critical_threshold
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Disk space check failed: {str(e)}",
                details={"error": str(e)}
            )

class MemoryHealthCheck(BaseHealthCheck):
    """Health check for memory usage"""
    
    def __init__(self):
        super().__init__("memory", timeout=5)
        self.warning_threshold = 0.8  # 80% used
        self.critical_threshold = 0.95  # 95% used
    
    async def _perform_check(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            
            used_percentage = memory.percent / 100
            available_gb = memory.available / (1024 ** 3)
            
            # Determine status
            if used_percentage >= self.critical_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {available_gb:.1f}GB available ({used_percentage:.1%} used)"
            elif used_percentage >= self.warning_threshold:
                status = HealthStatus.DEGRADED
                message = f"Warning: {available_gb:.1f}GB available ({used_percentage:.1%} used)"
            else:
                status = HealthStatus.HEALTHY
                message = f"Sufficient memory: {available_gb:.1f}GB available"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                details={
                    "total_gb": memory.total / (1024 ** 3),
                    "available_gb": available_gb,
                    "used_percentage": used_percentage,
                    "warning_threshold": self.warning_threshold,
                    "critical_threshold": self.critical_threshold
                }
            )
        
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)}
            )
```

### Phase 2: Graceful Degradation System

#### Create `grok/graceful_degradation/handler.py`
```python
"""
Graceful degradation handler for Grok CLI
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..health_check.core import HealthStatus, HealthCheckResult
from ..error_handling import ErrorHandler, ErrorCategory

class DegradationLevel(Enum):
    """Levels of service degradation"""
    FULL = "full"
    LIMITED = "limited"
    MINIMAL = "minimal"
    OFFLINE = "offline"

@dataclass
class ServiceCapability:
    """Service capability definition"""
    name: str
    dependencies: List[str]
    fallback_handler: Optional[Callable] = None
    degradation_message: str = ""

class GracefulDegradationHandler:
    """Handler for graceful service degradation"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.service_capabilities = {}
        self.current_degradation_level = DegradationLevel.FULL
        self.degraded_services = set()
        
        # Register default capabilities
        self._register_default_capabilities()
    
    def _register_default_capabilities(self):
        """Register default service capabilities"""
        self.register_capability(ServiceCapability(
            name="api_requests",
            dependencies=["xai_api", "network"],
            fallback_handler=self._api_fallback,
            degradation_message="API requests unavailable - using cached responses or offline mode"
        ))
        
        self.register_capability(ServiceCapability(
            name="code_diff",
            dependencies=["vscode"],
            fallback_handler=self._diff_fallback,
            degradation_message="VS Code diff unavailable - using basic text comparison"
        ))
        
        self.register_capability(ServiceCapability(
            name="project_analysis",
            dependencies=["system_tools"],
            fallback_handler=self._analysis_fallback,
            degradation_message="Some project analysis features limited due to missing tools"
        ))
        
        self.register_capability(ServiceCapability(
            name="file_operations",
            dependencies=["disk_space"],
            fallback_handler=self._file_ops_fallback,
            degradation_message="File operations limited due to low disk space"
        ))
    
    def register_capability(self, capability: ServiceCapability):
        """Register a service capability"""
        self.service_capabilities[capability.name] = capability
    
    def update_health_status(self, health_results: Dict[str, HealthCheckResult]):
        """Update degradation status based on health check results"""
        previously_degraded = self.degraded_services.copy()
        self.degraded_services.clear()
        
        # Check each service capability
        for capability_name, capability in self.service_capabilities.items():
            dependency_health = []
            
            for dep in capability.dependencies:
                if dep in health_results:
                    dependency_health.append(health_results[dep].status)
                else:
                    dependency_health.append(HealthStatus.UNKNOWN)
            
            # Determine if service should be degraded
            if any(status == HealthStatus.UNHEALTHY for status in dependency_health):
                self.degraded_services.add(capability_name)
                if capability_name not in previously_degraded:
                    self._notify_degradation(capability_name, capability.degradation_message)
            elif any(status == HealthStatus.DEGRADED for status in dependency_health):
                self.degraded_services.add(capability_name)
                if capability_name not in previously_degraded:
                    self._notify_degradation(capability_name, capability.degradation_message)
        
        # Update overall degradation level
        self._update_degradation_level()
        
        # Notify recovery for services that are no longer degraded
        recovered_services = previously_degraded - self.degraded_services
        for service in recovered_services:
            self._notify_recovery(service)
    
    def _update_degradation_level(self):
        """Update overall degradation level"""
        if not self.degraded_services:
            self.current_degradation_level = DegradationLevel.FULL
        elif len(self.degraded_services) == 1:
            self.current_degradation_level = DegradationLevel.LIMITED
        elif len(self.degraded_services) < len(self.service_capabilities):
            self.current_degradation_level = DegradationLevel.MINIMAL
        else:
            self.current_degradation_level = DegradationLevel.OFFLINE
    
    def _notify_degradation(self, service: str, message: str):
        """Notify about service degradation"""
        print(f"⚠️  Service degraded: {service}")
        print(f"   {message}")
    
    def _notify_recovery(self, service: str):
        """Notify about service recovery"""
        print(f"✅ Service recovered: {service}")
    
    def is_service_available(self, service: str) -> bool:
        """Check if a service is available"""
        return service not in self.degraded_services
    
    def get_fallback_handler(self, service: str) -> Optional[Callable]:
        """Get fallback handler for a service"""
        if service in self.service_capabilities:
            return self.service_capabilities[service].fallback_handler
        return None
    
    def execute_with_fallback(self, service: str, primary_func: Callable, *args, **kwargs) -> Any:
        """Execute function with fallback handling"""
        if self.is_service_available(service):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, {"service": service}
                )
                # Fall through to fallback
        
        # Use fallback handler
        fallback_handler = self.get_fallback_handler(service)
        if fallback_handler:
            return fallback_handler(*args, **kwargs)
        else:
            raise RuntimeError(f"Service '{service}' unavailable and no fallback configured")
    
    def _api_fallback(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback handler for API requests"""
        return {
            "error": "API unavailable",
            "fallback": True,
            "message": "Operating in offline mode"
        }
    
    def _diff_fallback(self, *args, **kwargs) -> str:
        """Fallback handler for code diff"""
        return "Code diff unavailable - VS Code not found. Using basic text comparison."
    
    def _analysis_fallback(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback handler for project analysis"""
        return {
            "analysis": "limited",
            "message": "Some analysis features unavailable due to missing system tools"
        }
    
    def _file_ops_fallback(self, *args, **kwargs) -> Dict[str, Any]:
        """Fallback handler for file operations"""
        return {
            "warning": "Low disk space - file operations may be limited",
            "available": False
        }
    
    def get_degradation_report(self) -> Dict[str, Any]:
        """Get comprehensive degradation report"""
        return {
            "degradation_level": self.current_degradation_level.value,
            "degraded_services": list(self.degraded_services),
            "available_services": [
                name for name in self.service_capabilities.keys()
                if name not in self.degraded_services
            ],
            "total_services": len(self.service_capabilities),
            "health_percentage": (
                (len(self.service_capabilities) - len(self.degraded_services)) / 
                len(self.service_capabilities) * 100
            ) if self.service_capabilities else 100
        }
```

### Phase 3: Startup Validation System

#### Create `grok/startup_validator.py`
```python
"""
Startup validation system for Grok CLI
"""

import asyncio
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

from .health_check.core import HealthCheckManager, HealthStatus
from .graceful_degradation.handler import GracefulDegradationHandler, DegradationLevel
from .error_handling import ErrorHandler, ErrorCategory
from .config import ConfigManager

class StartupValidator:
    """Validates system health at startup"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.error_handler = ErrorHandler()
        self.health_manager = HealthCheckManager(config_manager)
        self.degradation_handler = GracefulDegradationHandler()
        
        # Load configuration
        self.config = config_manager.load_settings()
        self.startup_config = self.config.get('startup', {})
        self.strict_mode = self.startup_config.get('strict_mode', False)
        self.required_services = self.startup_config.get('required_services', [])
    
    async def validate_startup(self) -> Dict[str, Any]:
        """Perform comprehensive startup validation"""
        print("🔍 Performing startup validation...")
        
        try:
            # Run all health checks
            health_results = await self.health_manager.check_all()
            
            # Update degradation status
            self.degradation_handler.update_health_status(health_results)
            
            # Get system health summary
            system_health = self.health_manager.get_system_health()
            
            # Get degradation report
            degradation_report = self.degradation_handler.get_degradation_report()
            
            # Validate critical services
            validation_result = self._validate_critical_services(health_results)
            
            # Generate startup report
            startup_report = {
                "validation_passed": validation_result["passed"],
                "system_health": system_health,
                "degradation_report": degradation_report,
                "critical_services": validation_result,
                "recommendations": self._generate_recommendations(health_results)
            }
            
            # Display startup summary
            self._display_startup_summary(startup_report)
            
            # Handle strict mode
            if self.strict_mode and not validation_result["passed"]:
                print("❌ Startup validation failed in strict mode")
                sys.exit(1)
            
            return startup_report
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM, {"operation": "startup_validation"}
            )
            return {"validation_passed": False, "error": str(e)}
    
    def _validate_critical_services(self, health_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate critical services"""
        critical_failures = []
        warnings = []
        
        # Check API connectivity (critical)
        if "xai_api" in health_results:
            api_result = health_results["xai_api"]
            if api_result.status == HealthStatus.UNHEALTHY:
                critical_failures.append("xAI API is not accessible")
            elif api_result.status == HealthStatus.DEGRADED:
                warnings.append("xAI API has connectivity issues")
        
        # Check required services
        for service in self.required_services:
            if service in health_results:
                result = health_results[service]
                if result.status == HealthStatus.UNHEALTHY:
                    critical_failures.append(f"Required service '{service}' is unhealthy")
        
        # Check system resources
        if "disk_space" in health_results:
            disk_result = health_results["disk_space"]
            if disk_result.status == HealthStatus.UNHEALTHY:
                critical_failures.append("Insufficient disk space")
        
        if "memory" in health_results:
            memory_result = health_results["memory"]
            if memory_result.status == HealthStatus.UNHEALTHY:
                critical_failures.append("Insufficient memory")
        
        return {
            "passed": len(critical_failures) == 0,
            "critical_failures": critical_failures,
            "warnings": warnings
        }
    
    def _generate_recommendations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate startup recommendations"""
        recommendations = []
        
        for check_name, result in health_results.items():
            if result.status == HealthStatus.UNHEALTHY:
                if check_name == "xai_api":
                    recommendations.append("Check your xAI API key configuration")
                elif check_name == "vscode":
                    recommendations.append("Install VS Code for enhanced diff functionality")
                elif check_name == "system_tools":
                    recommendations.append("Install missing system tools for full functionality")
                elif check_name == "network":
                    recommendations.append("Check network connectivity")
                elif check_name == "disk_space":
                    recommendations.append("Free up disk space")
                elif check_name == "memory":
                    recommendations.append("Close other applications to free memory")
        
        return recommendations
    
    def _display_startup_summary(self, report: Dict[str, Any]):
        """Display startup summary"""
        print("\n📊 Startup Validation Summary")
        print("=" * 40)
        
        # Overall status
        if report["validation_passed"]:
            print("✅ Startup validation passed")
        else:
            print("❌ Startup validation failed")
        
        # System health
        system_health = report["system_health"]
        print(f"🏥 System Health: {system_health['overall_status'].value}")
        print(f"📈 Health Score: {report['degradation_report']['health_percentage']:.1f}%")
        
        # Service status
        summary = system_health["summary"]
        print(f"🔧 Services: {summary['healthy']} healthy, {summary['degraded']} degraded, {summary['unhealthy']} unhealthy")
        
        # Degradation level
        degradation_level = report["degradation_report"]["degradation_level"]
        if degradation_level != "full":
            print(f"⚠️  Operating in {degradation_level} mode")
        
        # Critical failures
        critical_failures = report["critical_services"]["critical_failures"]
        if critical_failures:
            print("\n❌ Critical Issues:")
            for failure in critical_failures:
                print(f"  • {failure}")
        
        # Warnings
        warnings = report["critical_services"]["warnings"]
        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        # Recommendations
        recommendations = report["recommendations"]
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("=" * 40)
    
    def get_health_manager(self) -> HealthCheckManager:
        """Get health check manager"""
        return self.health_manager
    
    def get_degradation_handler(self) -> GracefulDegradationHandler:
        """Get graceful degradation handler"""
        return self.degradation_handler
```

## Implementation Steps for Claude Code

### Step 1: Create Health Check Framework
```
Task: Create comprehensive health check system

Instructions:
1. Create grok/health_check/ package with core framework
2. Implement base health check classes and manager
3. Add specific health checks for xAI API, VS Code, system tools
4. Create network connectivity and resource monitoring checks
5. Test health check accuracy and performance
```

### Step 2: Implement Graceful Degradation
```
Task: Create graceful degradation system

Instructions:
1. Create grok/graceful_degradation/ package
2. Implement service capability definitions and fallback handlers
3. Add degradation level management
4. Create fallback implementations for core services
5. Test degradation scenarios and recovery
```

### Step 3: Build Startup Validation
```
Task: Create startup validation system

Instructions:
1. Create grok/startup_validator.py with validation logic
2. Implement critical service validation
3. Add startup recommendations and reporting
4. Create strict mode for production environments
5. Test startup validation with various failure scenarios
```

### Step 4: Integration and CLI Commands
```
Task: Integrate health checks with CLI and add commands

Instructions:
1. Integrate health checks with main CLI startup
2. Add health check CLI commands (/health, /status)
3. Create health monitoring dashboard
4. Add configuration options for health checks
5. Test integrated health monitoring experience
```

## Testing Strategy

### Unit Tests
- Individual health check implementations
- Graceful degradation logic
- Startup validation rules
- Configuration handling

### Integration Tests
- End-to-end health check scenarios
- Fallback handler execution
- Startup validation with real dependencies
- Recovery after dependency restoration

### Performance Tests
- Health check execution time
- Resource usage during monitoring
- Concurrent health check performance

## Success Metrics
- Accurate dependency detection (>95%)
- Graceful degradation without crashes
- Clear user communication about issues
- Fast startup validation (<10 seconds)
- Reliable recovery after dependency restoration

## Next Steps
After completion of this task:
1. Reliable system operation under various conditions
2. Better user experience with clear status communication
3. Foundation for automated system monitoring
4. Improved system reliability and uptime