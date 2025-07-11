# Architecture: Task 007 - Improve Configuration Management System

## Overview
This task enhances the configuration management system with validation, schema support, migration capabilities, and environment-specific settings to provide a robust configuration framework.

## Technical Scope

### Files to Modify
- `grok/config.py` - Enhance existing configuration system
- `grok/config_schema.py` - New configuration schema definitions
- `grok/config_migration.py` - New configuration migration system

### Dependencies
- Task 006 (Error Handling) - Required for proper error management

## Implementation Details

### Phase 1: Configuration Schema System

#### Create `grok/config_schema.py`
```python
"""
Configuration schema definitions and validation for Grok CLI
"""

import json
import jsonschema
from typing import Dict, Any, Optional, List
from pathlib import Path

class ConfigSchema:
    """Configuration schema management"""
    
    def __init__(self):
        self.schemas = self._initialize_schemas()
    
    def _initialize_schemas(self) -> Dict[str, Dict]:
        """Initialize configuration schemas"""
        return {
            "1.0": {
                "type": "object",
                "properties": {
                    "version": {"type": "string", "enum": ["1.0"]},
                    "api_key": {"type": "string", "minLength": 1},
                    "model": {"type": "string", "default": "grok-4"},
                    "mode": {"type": "string", "enum": ["default", "auto-complete", "planning"]},
                    "permissions": {
                        "type": "object",
                        "properties": {
                            "allow": {"type": "array", "items": {"type": "string"}},
                            "deny": {"type": "array", "items": {"type": "string"}},
                            "allowed_cmds": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        },
                        "required": ["allow", "deny", "allowed_cmds"]
                    },
                    "mcp_servers": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "transport": {"type": "string", "enum": ["stdio", "http"]},
                                "command": {"type": "string"},
                                "args": {"type": "array", "items": {"type": "string"}},
                                "env": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"}
                                }
                            },
                            "required": ["transport", "command"]
                        }
                    },
                    "logging": {
                        "type": "object",
                        "properties": {
                            "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                            "file_enabled": {"type": "boolean"},
                            "console_enabled": {"type": "boolean"}
                        }
                    },
                    "security": {
                        "type": "object",
                        "properties": {
                            "rate_limits": {
                                "type": "object",
                                "properties": {
                                    "api_calls": {"type": "integer", "minimum": 1},
                                    "commands": {"type": "integer", "minimum": 1}
                                }
                            },
                            "dangerous_commands": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "environment": {"type": "string", "enum": ["development", "staging", "production"]}
                },
                "required": ["version", "permissions"]
            }
        }
    
    def validate_config(self, config: Dict[str, Any], version: str = "1.0") -> Dict[str, Any]:
        """Validate configuration against schema"""
        if version not in self.schemas:
            raise ValueError(f"Unknown configuration version: {version}")
        
        schema = self.schemas[version]
        
        try:
            jsonschema.validate(config, schema)
            return {"valid": True, "errors": []}
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "errors": [str(e)]
            }
        except jsonschema.SchemaError as e:
            return {
                "valid": False,
                "errors": [f"Schema error: {str(e)}"]
            }
    
    def get_default_config(self, version: str = "1.0") -> Dict[str, Any]:
        """Get default configuration for version"""
        if version not in self.schemas:
            raise ValueError(f"Unknown configuration version: {version}")
        
        return {
            "version": version,
            "model": "grok-4",
            "mode": "default",
            "permissions": {
                "allow": [],
                "deny": ["rm", "del", "format", "sudo"],
                "allowed_cmds": {}
            },
            "mcp_servers": {},
            "logging": {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True
            },
            "security": {
                "rate_limits": {
                    "api_calls": 100,
                    "commands": 50
                },
                "dangerous_commands": ["rm", "del", "format", "sudo", "chmod", "chown"]
            },
            "environment": "development"
        }
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported configuration versions"""
        return list(self.schemas.keys())
```

### Phase 2: Configuration Migration System

#### Create `grok/config_migration.py`
```python
"""
Configuration migration system for Grok CLI
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class ConfigMigration:
    """Configuration migration management"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.migrations = self._initialize_migrations()
    
    def _initialize_migrations(self) -> Dict[str, callable]:
        """Initialize migration functions"""
        return {
            "0.1_to_1.0": self._migrate_0_1_to_1_0,
            # Add more migrations as needed
        }
    
    def _migrate_0_1_to_1_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 0.1 to 1.0"""
        migrated = config.copy()
        
        # Add version field
        migrated["version"] = "1.0"
        
        # Update permissions structure
        if "permissions" in migrated:
            permissions = migrated["permissions"]
            if "allowed_cmds" not in permissions:
                permissions["allowed_cmds"] = {}
        
        # Add new fields with defaults
        if "logging" not in migrated:
            migrated["logging"] = {
                "level": "INFO",
                "file_enabled": True,
                "console_enabled": True
            }
        
        if "security" not in migrated:
            migrated["security"] = {
                "rate_limits": {
                    "api_calls": 100,
                    "commands": 50
                },
                "dangerous_commands": ["rm", "del", "format", "sudo", "chmod", "chown"]
            }
        
        if "environment" not in migrated:
            migrated["environment"] = "development"
        
        return migrated
    
    def detect_version(self, config: Dict[str, Any]) -> str:
        """Detect configuration version"""
        if "version" in config:
            return config["version"]
        
        # Legacy detection logic
        if "api_key" in config and "permissions" in config:
            return "0.1"
        
        return "unknown"
    
    def needs_migration(self, config: Dict[str, Any], target_version: str = "1.0") -> bool:
        """Check if configuration needs migration"""
        current_version = self.detect_version(config)
        return current_version != target_version and current_version != "unknown"
    
    def migrate_config(self, config: Dict[str, Any], target_version: str = "1.0") -> Dict[str, Any]:
        """Migrate configuration to target version"""
        current_version = self.detect_version(config)
        
        if current_version == target_version:
            return config
        
        # Create backup
        self._create_backup(config)
        
        # Apply migrations
        migrated = config.copy()
        
        if current_version == "0.1" and target_version == "1.0":
            migrated = self._migrate_0_1_to_1_0(migrated)
        
        return migrated
    
    def _create_backup(self, config: Dict[str, Any]) -> Path:
        """Create backup of current configuration"""
        backup_dir = self.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"config_backup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return backup_file
    
    def restore_backup(self, backup_file: Path) -> Dict[str, Any]:
        """Restore configuration from backup"""
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        with open(backup_file, 'r') as f:
            return json.load(f)
    
    def list_backups(self) -> List[Path]:
        """List available configuration backups"""
        backup_dir = self.config_dir / "backups"
        if not backup_dir.exists():
            return []
        
        return sorted(backup_dir.glob("config_backup_*.json"), reverse=True)
```

### Phase 3: Enhanced Configuration System

#### Update `grok/config.py`
```python
"""
Enhanced configuration management for Grok CLI
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config_schema import ConfigSchema
from .config_migration import ConfigMigration
from .error_handling import ErrorHandler, ErrorCategory

CONFIG_DIR = Path.home() / '.grok'
PROJECT_CONFIG = '.grok/settings.json'

class ConfigManager:
    """Enhanced configuration management"""
    
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config_dir.mkdir(exist_ok=True)
        self.schema = ConfigSchema()
        self.migration = ConfigMigration(self.config_dir)
        self.error_handler = ErrorHandler()
        self._current_config = None
    
    def load_settings(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration with validation and migration"""
        try:
            # Load user settings
            user_config = self._load_user_config()
            
            # Load project settings
            project_config = self._load_project_config()
            
            # Load environment-specific settings
            env_config = self._load_environment_config(environment)
            
            # Merge configurations (project > environment > user)
            merged_config = {**user_config, **env_config, **project_config}
            
            # Migrate if needed
            if self.migration.needs_migration(merged_config):
                merged_config = self.migration.migrate_config(merged_config)
                # Save migrated config
                self._save_user_config(merged_config)
            
            # Validate configuration
            validation_result = self.schema.validate_config(merged_config)
            if not validation_result["valid"]:
                raise ValueError(f"Configuration validation failed: {validation_result['errors']}")
            
            self._current_config = merged_config
            return merged_config
            
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION, {"operation": "load_settings"}
            )
            # Return default configuration on error
            return self.schema.get_default_config()
    
    def _load_user_config(self) -> Dict[str, Any]:
        """Load user-level configuration"""
        user_config_path = self.config_dir / 'settings.json'
        if user_config_path.exists():
            try:
                with open(user_config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return self.schema.get_default_config()
    
    def _load_project_config(self) -> Dict[str, Any]:
        """Load project-level configuration"""
        project_config_path = Path.cwd() / PROJECT_CONFIG
        if project_config_path.exists():
            try:
                with open(project_config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {}
    
    def _load_environment_config(self, environment: Optional[str]) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        if not environment:
            return {}
        
        env_config_path = self.config_dir / f'settings.{environment}.json'
        if env_config_path.exists():
            try:
                with open(env_config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {}
    
    def save_settings(self, settings: Dict[str, Any], project: bool = False, 
                     environment: Optional[str] = None) -> bool:
        """Save configuration with validation"""
        try:
            # Validate before saving
            validation_result = self.schema.validate_config(settings)
            if not validation_result["valid"]:
                raise ValueError(f"Configuration validation failed: {validation_result['errors']}")
            
            if environment:
                # Save environment-specific config
                env_config_path = self.config_dir / f'settings.{environment}.json'
                with open(env_config_path, 'w') as f:
                    json.dump(settings, f, indent=2)
            elif project:
                # Save project config
                project_config_path = Path.cwd() / PROJECT_CONFIG
                project_config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(project_config_path, 'w') as f:
                    json.dump(settings, f, indent=2)
            else:
                # Save user config
                self._save_user_config(settings)
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION, {"operation": "save_settings"}
            )
            return False
    
    def _save_user_config(self, settings: Dict[str, Any]):
        """Save user-level configuration"""
        user_config_path = self.config_dir / 'settings.json'
        with open(user_config_path, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration"""
        return self.schema.validate_config(config)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return self.schema.get_default_config()
    
    def backup_config(self) -> Path:
        """Create backup of current configuration"""
        if not self._current_config:
            self._current_config = self.load_settings()
        
        return self.migration._create_backup(self._current_config)
    
    def restore_config(self, backup_file: Path) -> bool:
        """Restore configuration from backup"""
        try:
            restored_config = self.migration.restore_backup(backup_file)
            return self.save_settings(restored_config)
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION, {"operation": "restore_config"}
            )
            return False
    
    def list_backups(self) -> List[Path]:
        """List available configuration backups"""
        return self.migration.list_backups()

# Initialize global config manager
config_manager = ConfigManager()

# Legacy functions for backward compatibility
def load_settings():
    return config_manager.load_settings()

def save_settings(settings, project=False):
    return config_manager.save_settings(settings, project)

def get_api_key():
    settings = config_manager.load_settings()
    return settings.get('api_key')

def set_api_key(key):
    settings = config_manager.load_settings()
    settings['api_key'] = key
    config_manager.save_settings(settings)

def get_mode():
    settings = config_manager.load_settings()
    return settings.get('mode', 'default')

def set_mode(mode):
    settings = config_manager.load_settings()
    settings['mode'] = mode
    config_manager.save_settings(settings)

def get_permissions():
    settings = config_manager.load_settings()
    return settings.get('permissions', {'allow': [], 'deny': [], 'allowed_cmds': {}})

def update_permissions(permissions):
    settings = config_manager.load_settings()
    settings['permissions'] = permissions
    config_manager.save_settings(settings)

def get_mcp_servers():
    settings = config_manager.load_settings()
    return settings.get('mcp_servers', {})

def update_mcp_servers(mcp_servers):
    settings = config_manager.load_settings()
    settings['mcp_servers'] = mcp_servers
    config_manager.save_settings(settings)
```

## Implementation Steps for Claude Code

### Step 1: Create Configuration Schema System
```
Task: Create comprehensive configuration schema and validation

Instructions:
1. Create grok/config_schema.py with ConfigSchema class
2. Define JSON schema for configuration validation
3. Implement validation methods and error handling
4. Add default configuration generation
5. Test schema validation with various configuration files
```

### Step 2: Create Configuration Migration System
```
Task: Implement configuration migration framework

Instructions:
1. Create grok/config_migration.py with ConfigMigration class
2. Implement version detection and migration logic
3. Add backup and restore functionality
4. Create migration functions for version transitions
5. Test migration with different configuration versions
```

### Step 3: Enhance Configuration Manager
```
Task: Enhance existing configuration system

Instructions:
1. Update grok/config.py with enhanced ConfigManager class
2. Integrate schema validation and migration
3. Add environment-specific configuration support
4. Implement backup and restore operations
5. Maintain backward compatibility with existing functions
6. Test enhanced configuration system thoroughly
```

### Step 4: Add Configuration CLI Commands
```
Task: Add configuration management CLI commands

Instructions:
1. Add configuration validation command
2. Add configuration backup/restore commands
3. Add environment switching commands
4. Add configuration migration commands
5. Test all CLI configuration operations
```

## Testing Strategy

### Unit Tests
- Schema validation accuracy
- Migration logic correctness
- Configuration loading and saving
- Error handling integration

### Integration Tests
- Environment-specific configurations
- Backup and restore operations
- Migration between versions
- CLI command functionality

## Success Metrics
- Robust configuration validation
- Seamless configuration migration
- Environment-specific settings
- Reliable backup/restore operations
- Comprehensive error handling

## Next Steps
After completion of this task:
1. Task 008 (Plugin Architecture) can use enhanced configuration
2. All configuration operations become more reliable
3. Environment-specific deployments are supported