# Architecture: Task 004 - Implement Development Workflow Tools

## Overview
This task implements essential development workflow tools that provide automated support for testing, linting, git operations, and dependency management. The tools will integrate with the existing security framework and file operations to provide a comprehensive development experience.

## Technical Scope

### Files to Modify
- `grok/tools.py` - Add new development tools
- `grok/dev_tools.py` - New development tools module
- `grok/project_detector.py` - New project type detection module
- `grok/framework_adapters.py` - New framework-specific adapters

### Dependencies
- Task 001 (Import Fixes) - Required for stable imports
- Task 002 (Security Framework) - Required for secure command execution
- Task 003 (File Operations) - Required for file system operations

## Architectural Approach

### 1. Development Tools Architecture
```
Development Tools Layer
    ↓
Framework Detection Layer
    ↓
Security Validation Layer (from Task 002)
    ↓
File Operations Layer (from Task 003)
    ↓
System Command Execution
```

### 2. Tool Components

#### A. Test Runner (`run_tests`)
- Framework auto-detection (pytest, unittest, jest, etc.)
- Test discovery and execution
- Result parsing and formatting
- Performance tracking

#### B. Code Linter (`lint_code`)
- Multi-linter support (pylint, flake8, eslint, etc.)
- Configuration file discovery
- Result standardization
- Fix suggestions

#### C. Git Operations (`git_operations`)
- Repository status and information
- Staging and commit operations
- Branch management
- Remote operations

#### D. Dependency Manager (`install_dependencies`)
- Package manager detection
- Dependency installation
- Virtual environment management
- Security scanning

## Implementation Details

### Phase 1: Project Detection Framework

#### Create `grok/project_detector.py`
```python
"""
Project type detection and framework identification
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ProjectType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    UNKNOWN = "unknown"

@dataclass
class ProjectInfo:
    """Project information structure"""
    project_type: ProjectType
    frameworks: List[str]
    package_manager: Optional[str]
    test_framework: Optional[str]
    linter: Optional[str]
    build_system: Optional[str]
    config_files: List[str]
    entry_points: List[str]

class ProjectDetector:
    """Detect project type and associated tools"""
    
    def __init__(self):
        self.detection_rules = self._initialize_detection_rules()
    
    def _initialize_detection_rules(self) -> Dict:
        """Initialize project detection rules"""
        return {
            ProjectType.PYTHON: {
                'indicators': [
                    'requirements.txt', 'setup.py', 'pyproject.toml',
                    'Pipfile', 'poetry.lock', 'environment.yml'
                ],
                'extensions': ['.py'],
                'frameworks': {
                    'django': ['manage.py', 'settings.py', 'wsgi.py'],
                    'flask': ['app.py', 'wsgi.py'],
                    'fastapi': ['main.py', 'app.py'],
                    'pytest': ['pytest.ini', 'conftest.py', 'test_*.py'],
                    'unittest': ['test_*.py', '*_test.py']
                },
                'package_managers': ['pip', 'poetry', 'pipenv', 'conda'],
                'linters': ['pylint', 'flake8', 'black', 'mypy'],
                'test_frameworks': ['pytest', 'unittest', 'nose2']
            },
            ProjectType.JAVASCRIPT: {
                'indicators': [
                    'package.json', 'package-lock.json', 'yarn.lock',
                    'bower.json', 'jsconfig.json'
                ],
                'extensions': ['.js', '.jsx'],
                'frameworks': {
                    'react': ['package.json:react'],
                    'vue': ['package.json:vue'],
                    'angular': ['package.json:@angular'],
                    'express': ['package.json:express'],
                    'next': ['package.json:next']
                },
                'package_managers': ['npm', 'yarn', 'pnpm'],
                'linters': ['eslint', 'jshint', 'prettier'],
                'test_frameworks': ['jest', 'mocha', 'jasmine']
            },
            ProjectType.TYPESCRIPT: {
                'indicators': [
                    'tsconfig.json', 'package.json', 'yarn.lock',
                    'package-lock.json'
                ],
                'extensions': ['.ts', '.tsx'],
                'frameworks': {
                    'angular': ['package.json:@angular'],
                    'react': ['package.json:react', 'package.json:@types/react'],
                    'nest': ['package.json:@nestjs'],
                    'express': ['package.json:express']
                },
                'package_managers': ['npm', 'yarn', 'pnpm'],
                'linters': ['eslint', 'tslint', 'prettier'],
                'test_frameworks': ['jest', 'mocha', 'jasmine']
            },
            ProjectType.JAVA: {
                'indicators': [
                    'pom.xml', 'build.gradle', 'gradle.properties',
                    'build.xml', 'ivy.xml'
                ],
                'extensions': ['.java'],
                'frameworks': {
                    'spring': ['pom.xml:spring', 'build.gradle:spring'],
                    'maven': ['pom.xml'],
                    'gradle': ['build.gradle']
                },
                'package_managers': ['maven', 'gradle'],
                'linters': ['checkstyle', 'spotbugs', 'pmd'],
                'test_frameworks': ['junit', 'testng']
            },
            ProjectType.GO: {
                'indicators': ['go.mod', 'go.sum', 'Gopkg.toml', 'Gopkg.lock'],
                'extensions': ['.go'],
                'frameworks': {
                    'gin': ['go.mod:gin'],
                    'echo': ['go.mod:echo'],
                    'fiber': ['go.mod:fiber']
                },
                'package_managers': ['go'],
                'linters': ['golint', 'gofmt', 'go vet'],
                'test_frameworks': ['go test']
            },
            ProjectType.RUST: {
                'indicators': ['Cargo.toml', 'Cargo.lock'],
                'extensions': ['.rs'],
                'frameworks': {
                    'actix': ['Cargo.toml:actix'],
                    'rocket': ['Cargo.toml:rocket'],
                    'warp': ['Cargo.toml:warp']
                },
                'package_managers': ['cargo'],
                'linters': ['rustfmt', 'clippy'],
                'test_frameworks': ['cargo test']
            }
        }
    
    def detect_project(self, path: str = ".") -> ProjectInfo:
        """Detect project type and configuration"""
        project_path = Path(path).resolve()
        
        # Scan for indicator files
        found_files = []
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                found_files.append(file_path.name)
        
        # Detect project type
        detected_type = ProjectType.UNKNOWN
        confidence_scores = {}
        
        for project_type, rules in self.detection_rules.items():
            score = 0
            for indicator in rules['indicators']:
                if indicator in found_files:
                    score += 1
            
            # Check for file extensions
            for ext in rules['extensions']:
                if any(f.endswith(ext) for f in found_files):
                    score += 0.5
            
            confidence_scores[project_type] = score
        
        # Select project type with highest confidence
        if confidence_scores:
            detected_type = max(confidence_scores, key=confidence_scores.get)
            if confidence_scores[detected_type] == 0:
                detected_type = ProjectType.UNKNOWN
        
        # Detect frameworks and tools
        if detected_type != ProjectType.UNKNOWN:
            rules = self.detection_rules[detected_type]
            
            # Detect frameworks
            frameworks = []
            for framework, indicators in rules['frameworks'].items():
                if self._check_framework_indicators(project_path, indicators):
                    frameworks.append(framework)
            
            # Detect package manager
            package_manager = None
            for pm in rules['package_managers']:
                if self._check_package_manager(project_path, pm):
                    package_manager = pm
                    break
            
            # Detect test framework
            test_framework = None
            for tf in rules['test_frameworks']:
                if self._check_test_framework(project_path, tf):
                    test_framework = tf
                    break
            
            # Detect linter
            linter = None
            for lint in rules['linters']:
                if self._check_linter(project_path, lint):
                    linter = lint
                    break
            
            return ProjectInfo(
                project_type=detected_type,
                frameworks=frameworks,
                package_manager=package_manager,
                test_framework=test_framework,
                linter=linter,
                build_system=package_manager,
                config_files=self._find_config_files(project_path, detected_type),
                entry_points=self._find_entry_points(project_path, detected_type)
            )
        
        return ProjectInfo(
            project_type=ProjectType.UNKNOWN,
            frameworks=[],
            package_manager=None,
            test_framework=None,
            linter=None,
            build_system=None,
            config_files=[],
            entry_points=[]
        )
    
    def _check_framework_indicators(self, project_path: Path, indicators: List[str]) -> bool:
        """Check if framework indicators are present"""
        for indicator in indicators:
            if ':' in indicator:
                # Check package.json dependencies
                file_name, dep_name = indicator.split(':', 1)
                if self._check_package_dependency(project_path, file_name, dep_name):
                    return True
            else:
                # Check file existence
                if (project_path / indicator).exists():
                    return True
        return False
    
    def _check_package_dependency(self, project_path: Path, file_name: str, dep_name: str) -> bool:
        """Check if package dependency exists in package file"""
        try:
            if file_name == 'package.json':
                package_file = project_path / 'package.json'
                if package_file.exists():
                    with open(package_file, 'r') as f:
                        data = json.load(f)
                        deps = data.get('dependencies', {})
                        dev_deps = data.get('devDependencies', {})
                        return dep_name in deps or dep_name in dev_deps
            
            elif file_name == 'pom.xml':
                pom_file = project_path / 'pom.xml'
                if pom_file.exists():
                    with open(pom_file, 'r') as f:
                        content = f.read()
                        return dep_name in content
            
            elif file_name == 'Cargo.toml':
                cargo_file = project_path / 'Cargo.toml'
                if cargo_file.exists():
                    with open(cargo_file, 'r') as f:
                        content = f.read()
                        return dep_name in content
                        
        except Exception:
            pass
        
        return False
    
    def _check_package_manager(self, project_path: Path, pm: str) -> bool:
        """Check if package manager is available"""
        pm_indicators = {
            'npm': ['package.json', 'package-lock.json'],
            'yarn': ['yarn.lock', 'package.json'],
            'pip': ['requirements.txt', 'setup.py'],
            'poetry': ['pyproject.toml', 'poetry.lock'],
            'cargo': ['Cargo.toml'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle']
        }
        
        if pm in pm_indicators:
            return any((project_path / indicator).exists() for indicator in pm_indicators[pm])
        
        return False
    
    def _check_test_framework(self, project_path: Path, tf: str) -> bool:
        """Check if test framework is configured"""
        tf_indicators = {
            'pytest': ['pytest.ini', 'conftest.py', 'tests/', 'test_*.py'],
            'unittest': ['test_*.py', '*_test.py'],
            'jest': ['jest.config.js', 'package.json'],
            'mocha': ['mocha.opts', '.mocharc.json', 'package.json'],
            'junit': ['pom.xml', 'build.gradle']
        }
        
        if tf in tf_indicators:
            for indicator in tf_indicators[tf]:
                if '*' in indicator:
                    # Pattern matching
                    if list(project_path.glob(f"**/{indicator}")):
                        return True
                else:
                    # Direct file check
                    if (project_path / indicator).exists():
                        return True
        
        return False
    
    def _check_linter(self, project_path: Path, linter: str) -> bool:
        """Check if linter is configured"""
        linter_configs = {
            'pylint': ['.pylintrc', 'pylint.cfg'],
            'flake8': ['.flake8', 'tox.ini', 'setup.cfg'],
            'eslint': ['.eslintrc.js', '.eslintrc.json', '.eslintrc.yml'],
            'tslint': ['tslint.json'],
            'prettier': ['.prettierrc', 'prettier.config.js']
        }
        
        if linter in linter_configs:
            return any((project_path / config).exists() for config in linter_configs[linter])
        
        return False
    
    def _find_config_files(self, project_path: Path, project_type: ProjectType) -> List[str]:
        """Find configuration files for project type"""
        config_patterns = {
            ProjectType.PYTHON: ['*.cfg', '*.ini', '*.toml', 'requirements*.txt'],
            ProjectType.JAVASCRIPT: ['package.json', '*.config.js', '.*rc.js'],
            ProjectType.TYPESCRIPT: ['tsconfig.json', '*.config.ts', '.*rc.ts'],
            ProjectType.JAVA: ['pom.xml', 'build.gradle', '*.properties'],
            ProjectType.GO: ['go.mod', 'go.sum'],
            ProjectType.RUST: ['Cargo.toml', 'Cargo.lock']
        }
        
        config_files = []
        if project_type in config_patterns:
            for pattern in config_patterns[project_type]:
                config_files.extend([str(f) for f in project_path.glob(pattern)])
        
        return config_files
    
    def _find_entry_points(self, project_path: Path, project_type: ProjectType) -> List[str]:
        """Find entry points for project type"""
        entry_patterns = {
            ProjectType.PYTHON: ['main.py', 'app.py', 'run.py', 'manage.py'],
            ProjectType.JAVASCRIPT: ['index.js', 'app.js', 'server.js', 'main.js'],
            ProjectType.TYPESCRIPT: ['index.ts', 'app.ts', 'server.ts', 'main.ts'],
            ProjectType.JAVA: ['Main.java', 'Application.java'],
            ProjectType.GO: ['main.go'],
            ProjectType.RUST: ['main.rs', 'lib.rs']
        }
        
        entry_points = []
        if project_type in entry_patterns:
            for pattern in entry_patterns[project_type]:
                matches = list(project_path.rglob(pattern))
                entry_points.extend([str(f) for f in matches])
        
        return entry_points
```

### Phase 2: Development Tools Implementation

#### Create `grok/dev_tools.py`
```python
"""
Development workflow tools for Grok CLI
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .security import SecurityManager
from .project_detector import ProjectDetector, ProjectInfo, ProjectType
from .file_operations import FileOperations

@dataclass
class TestResult:
    """Test execution result"""
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    output: str
    errors: List[str]

@dataclass
class LintResult:
    """Linting result"""
    success: bool
    total_issues: int
    errors: int
    warnings: int
    info: int
    issues: List[Dict[str, Any]]
    output: str

class DevTools:
    """Development workflow tools"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.detector = ProjectDetector()
        self.file_ops = FileOperations(security_manager)
    
    def run_tests(self, path: str = ".", test_pattern: Optional[str] = None,
                  verbose: bool = False) -> Dict:
        """Run tests with framework auto-detection"""
        try:
            project_path = Path(path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(project_path), 'test'):
                return {'error': 'Test execution denied for security reasons'}
            
            # Detect project configuration
            project_info = self.detector.detect_project(str(project_path))
            
            if not project_info.test_framework:
                return {'error': 'No test framework detected'}
            
            # Execute tests based on framework
            if project_info.test_framework == 'pytest':
                return self._run_pytest(project_path, test_pattern, verbose)
            elif project_info.test_framework == 'unittest':
                return self._run_unittest(project_path, test_pattern, verbose)
            elif project_info.test_framework == 'jest':
                return self._run_jest(project_path, test_pattern, verbose)
            elif project_info.test_framework == 'mocha':
                return self._run_mocha(project_path, test_pattern, verbose)
            elif project_info.test_framework == 'junit':
                return self._run_junit(project_path, test_pattern, verbose)
            else:
                return {'error': f'Unsupported test framework: {project_info.test_framework}'}
                
        except Exception as e:
            return {'error': f'Error running tests: {e}'}
    
    def _run_pytest(self, project_path: Path, test_pattern: Optional[str], verbose: bool) -> Dict:
        """Run pytest tests"""
        cmd = ['python', '-m', 'pytest']
        
        if verbose:
            cmd.append('-v')
        
        if test_pattern:
            cmd.extend(['-k', test_pattern])
        
        cmd.append('--json-report')
        cmd.append('--json-report-file=/tmp/pytest_report.json')
        
        result = self._execute_command(cmd, project_path)
        
        # Parse pytest JSON report
        try:
            with open('/tmp/pytest_report.json', 'r') as f:
                report = json.load(f)
            
            return {
                'success': result.returncode == 0,
                'framework': 'pytest',
                'total_tests': report.get('summary', {}).get('total', 0),
                'passed_tests': report.get('summary', {}).get('passed', 0),
                'failed_tests': report.get('summary', {}).get('failed', 0),
                'skipped_tests': report.get('summary', {}).get('skipped', 0),
                'execution_time': report.get('duration', 0),
                'output': result.stdout,
                'errors': result.stderr.splitlines() if result.stderr else []
            }
            
        except Exception:
            return self._parse_generic_test_output(result, 'pytest')
    
    def _run_unittest(self, project_path: Path, test_pattern: Optional[str], verbose: bool) -> Dict:
        """Run unittest tests"""
        cmd = ['python', '-m', 'unittest']
        
        if verbose:
            cmd.append('-v')
        
        if test_pattern:
            cmd.extend(['discover', '-p', test_pattern])
        else:
            cmd.append('discover')
        
        result = self._execute_command(cmd, project_path)
        return self._parse_generic_test_output(result, 'unittest')
    
    def _run_jest(self, project_path: Path, test_pattern: Optional[str], verbose: bool) -> Dict:
        """Run Jest tests"""
        cmd = ['npm', 'test']
        
        if verbose:
            cmd.append('--verbose')
        
        if test_pattern:
            cmd.extend(['--testNamePattern', test_pattern])
        
        cmd.append('--json')
        
        result = self._execute_command(cmd, project_path)
        
        # Parse Jest JSON output
        try:
            output_lines = result.stdout.splitlines()
            json_line = None
            for line in reversed(output_lines):
                if line.strip().startswith('{'):
                    json_line = line
                    break
            
            if json_line:
                report = json.loads(json_line)
                return {
                    'success': report.get('success', False),
                    'framework': 'jest',
                    'total_tests': report.get('numTotalTests', 0),
                    'passed_tests': report.get('numPassedTests', 0),
                    'failed_tests': report.get('numFailedTests', 0),
                    'skipped_tests': report.get('numPendingTests', 0),
                    'execution_time': report.get('executionTime', 0),
                    'output': result.stdout,
                    'errors': result.stderr.splitlines() if result.stderr else []
                }
        except Exception:
            pass
        
        return self._parse_generic_test_output(result, 'jest')
    
    def lint_code(self, path: str = ".", fix: bool = False) -> Dict:
        """Run code linting with auto-detection"""
        try:
            project_path = Path(path).resolve()
            
            # Security validation
            if not self.security.validate_file_operation(str(project_path), 'lint'):
                return {'error': 'Linting denied for security reasons'}
            
            # Detect project configuration
            project_info = self.detector.detect_project(str(project_path))
            
            if not project_info.linter:
                return {'error': 'No linter detected'}
            
            # Execute linting based on detected linter
            if project_info.linter == 'pylint':
                return self._run_pylint(project_path, fix)
            elif project_info.linter == 'flake8':
                return self._run_flake8(project_path, fix)
            elif project_info.linter == 'eslint':
                return self._run_eslint(project_path, fix)
            elif project_info.linter == 'tslint':
                return self._run_tslint(project_path, fix)
            else:
                return {'error': f'Unsupported linter: {project_info.linter}'}
                
        except Exception as e:
            return {'error': f'Error running linter: {e}'}
    
    def _run_pylint(self, project_path: Path, fix: bool) -> Dict:
        """Run pylint"""
        cmd = ['python', '-m', 'pylint']
        
        # Find Python files
        python_files = list(project_path.glob('**/*.py'))
        if not python_files:
            return {'error': 'No Python files found'}
        
        cmd.extend([str(f) for f in python_files])
        cmd.append('--output-format=json')
        
        result = self._execute_command(cmd, project_path)
        
        # Parse pylint JSON output
        try:
            if result.stdout:
                issues = json.loads(result.stdout)
                errors = sum(1 for issue in issues if issue['type'] == 'error')
                warnings = sum(1 for issue in issues if issue['type'] == 'warning')
                
                return {
                    'success': result.returncode == 0,
                    'linter': 'pylint',
                    'total_issues': len(issues),
                    'errors': errors,
                    'warnings': warnings,
                    'info': len(issues) - errors - warnings,
                    'issues': issues,
                    'output': result.stdout
                }
        except Exception:
            pass
        
        return self._parse_generic_lint_output(result, 'pylint')
    
    def git_operations(self, operation: str, **kwargs) -> Dict:
        """Git operations with safety checks"""
        try:
            # Security validation
            if not self.security.validate_command(f'git {operation}'):
                return {'error': 'Git operation denied for security reasons'}
            
            if operation == 'status':
                return self._git_status()
            elif operation == 'add':
                return self._git_add(kwargs.get('files', []))
            elif operation == 'commit':
                return self._git_commit(kwargs.get('message', ''))
            elif operation == 'push':
                return self._git_push()
            elif operation == 'pull':
                return self._git_pull()
            elif operation == 'diff':
                return self._git_diff(kwargs.get('files', []))
            else:
                return {'error': f'Unsupported git operation: {operation}'}
                
        except Exception as e:
            return {'error': f'Error executing git operation: {e}'}
    
    def _git_status(self) -> Dict:
        """Get git status"""
        cmd = ['git', 'status', '--porcelain=v1']
        result = self._execute_command(cmd, Path.cwd())
        
        if result.returncode != 0:
            return {'error': 'Not a git repository or git error'}
        
        # Parse git status output
        files = {'modified': [], 'added': [], 'deleted': [], 'untracked': []}
        
        for line in result.stdout.splitlines():
            if line.startswith(' M '):
                files['modified'].append(line[3:])
            elif line.startswith('A  '):
                files['added'].append(line[3:])
            elif line.startswith(' D '):
                files['deleted'].append(line[3:])
            elif line.startswith('??'):
                files['untracked'].append(line[3:])
        
        return {
            'success': True,
            'operation': 'status',
            'files': files,
            'output': result.stdout
        }
    
    def install_dependencies(self, package_manager: Optional[str] = None) -> Dict:
        """Install dependencies with package manager auto-detection"""
        try:
            project_path = Path.cwd()
            
            # Security validation
            if not self.security.validate_command('install dependencies'):
                return {'error': 'Dependency installation denied for security reasons'}
            
            # Detect project and package manager
            project_info = self.detector.detect_project(str(project_path))
            
            if package_manager:
                pm = package_manager
            elif project_info.package_manager:
                pm = project_info.package_manager
            else:
                return {'error': 'No package manager detected'}
            
            # Execute installation based on package manager
            if pm == 'pip':
                return self._install_pip()
            elif pm == 'poetry':
                return self._install_poetry()
            elif pm == 'npm':
                return self._install_npm()
            elif pm == 'yarn':
                return self._install_yarn()
            elif pm == 'cargo':
                return self._install_cargo()
            else:
                return {'error': f'Unsupported package manager: {pm}'}
                
        except Exception as e:
            return {'error': f'Error installing dependencies: {e}'}
    
    def _install_pip(self) -> Dict:
        """Install Python dependencies with pip"""
        if Path('requirements.txt').exists():
            cmd = ['pip', 'install', '-r', 'requirements.txt']
        else:
            return {'error': 'No requirements.txt found'}
        
        result = self._execute_command(cmd, Path.cwd())
        
        return {
            'success': result.returncode == 0,
            'package_manager': 'pip',
            'output': result.stdout,
            'errors': result.stderr.splitlines() if result.stderr else []
        }
    
    def _execute_command(self, cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
        """Execute command with security checks"""
        # Final security validation
        cmd_str = ' '.join(cmd)
        if not self.security.validate_command(cmd_str):
            raise SecurityError(f"Command blocked: {cmd_str}")
        
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
    
    def _parse_generic_test_output(self, result: subprocess.CompletedProcess, framework: str) -> Dict:
        """Parse generic test output"""
        return {
            'success': result.returncode == 0,
            'framework': framework,
            'output': result.stdout,
            'errors': result.stderr.splitlines() if result.stderr else []
        }
    
    def _parse_generic_lint_output(self, result: subprocess.CompletedProcess, linter: str) -> Dict:
        """Parse generic lint output"""
        return {
            'success': result.returncode == 0,
            'linter': linter,
            'output': result.stdout,
            'errors': result.stderr.splitlines() if result.stderr else []
        }
```

### Phase 3: Tool Integration

#### Update `grok/tools.py`
```python
# Add development tools to TOOLS list
from .dev_tools import DevTools

# Initialize dev tools
dev_tools = DevTools(security_manager)

# Add new tools to TOOLS list
TOOLS.extend([
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run tests with framework auto-detection",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to test directory"},
                    "test_pattern": {"type": "string", "description": "Test pattern to match"},
                    "verbose": {"type": "boolean", "description": "Verbose output"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lint_code",
            "description": "Run code linting with auto-detection",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to lint"},
                    "fix": {"type": "boolean", "description": "Auto-fix issues"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_operations",
            "description": "Git operations with safety checks",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Git operation (status, add, commit, push, pull, diff)"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files for operation"},
                    "message": {"type": "string", "description": "Commit message"}
                },
                "required": ["operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_dependencies",
            "description": "Install dependencies with package manager auto-detection",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_manager": {"type": "string", "description": "Package manager to use"}
                },
                "required": [],
            },
        },
    }
])

# Add tool handlers
def handle_tool_call(tool_call, mode, permissions):
    # ... existing handlers ...
    
    if func_name == "run_tests":
        result = dev_tools.run_tests(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "lint_code":
        result = dev_tools.lint_code(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "git_operations":
        result = dev_tools.git_operations(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
    
    elif func_name == "install_dependencies":
        result = dev_tools.install_dependencies(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result)}
```

## Implementation Steps for Claude Code

### Step 1: Create Project Detection Framework
```
Task: Create project type detection and framework identification system

Instructions:
1. Create grok/project_detector.py with ProjectDetector class
2. Implement project type detection based on file indicators
3. Add framework and tool detection capabilities
4. Create comprehensive detection rules for major project types
5. Test detection accuracy with various project types
```

### Step 2: Implement Development Tools
```
Task: Create comprehensive development tools module

Instructions:
1. Create grok/dev_tools.py with DevTools class
2. Implement run_tests method with multi-framework support
3. Implement lint_code method with multi-linter support
4. Implement git_operations method with safety checks
5. Implement install_dependencies method with package manager detection
6. Test each tool with appropriate project types
```

### Step 3: Integrate with Tools Framework
```
Task: Integrate development tools with existing tools system

Instructions:
1. Update grok/tools.py to import and initialize dev tools
2. Add new tool definitions to TOOLS list
3. Add tool handlers to handle_tool_call function
4. Test integration through CLI interface
5. Verify security validation is working properly
```

### Step 4: Framework-Specific Adapters
```
Task: Create framework-specific adapters and optimizations

Instructions:
1. Create grok/framework_adapters.py for framework-specific logic
2. Implement output parsers for different frameworks
3. Add configuration file discovery and handling
4. Create unified result formatting
5. Test with multiple frameworks and project types
```

## Testing Strategy

### Unit Tests
- Project detection accuracy
- Tool execution with mocked commands
- Result parsing and formatting
- Security validation integration

### Integration Tests
- Real framework integration
- Cross-platform compatibility
- Performance with large projects

### Framework Coverage Tests
- Python (pytest, unittest)
- JavaScript/TypeScript (Jest, Mocha)
- Java (JUnit)
- Go (go test)
- Rust (cargo test)

## Success Metrics
- Accurate project type detection (>90%)
- Successful tool execution across frameworks
- Proper security validation
- Comprehensive result formatting
- Performance within acceptable limits

## Next Steps
After completion of this task:
1. Task 005 (Network Tools) can add external service integration
2. Enhanced development workflows become possible
3. CI/CD integration foundation is established