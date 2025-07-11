# Architecture: Task 001 - Fix Critical Import Dependencies and Session Management

## Overview
This task addresses foundational issues that are blocking basic functionality. These fixes are prerequisites for all subsequent development work and must be completed first to ensure system stability.

## Technical Scope

### Files to Modify
- `grok/agent.py` - Fix imports and session management
- `grok/tools.py` - Fix missing import
- `grok/config.py` - Add missing function exports

### Dependencies
- None (foundational task)

## Architectural Approach

### 1. Import Dependency Resolution
The current codebase has missing imports that cause runtime failures. We need to establish a proper import hierarchy and dependency chain.

### 2. Session Management Refactoring
Replace direct prompt_toolkit calls with proper session instance usage to ensure consistent prompt handling across the application.

### 3. API Key Security Enhancement
Move from global API key setting to per-request passing for better security and testing capabilities.

## Implementation Details

### Phase 1: Fix Missing Imports

#### Files to Update: `grok/agent.py`
**Current Issues:**
- Line 61: `get_permissions()` called but not imported
- Line 68: `prompt_toolkit.prompt()` used but not imported

**Solution:**
```python
# Add these imports at the top of agent.py
from .config import get_permissions
from prompt_toolkit import prompt
```

#### Files to Update: `grok/tools.py`
**Current Issues:**
- Line 105: `update_permissions()` called but not imported

**Solution:**
```python
# Add this import at the top of tools.py
from .config import update_permissions
```

#### Files to Update: `grok/config.py`
**Current Issues:**
- Functions are defined but may not be properly exported

**Solution:**
```python
# Ensure all functions are properly defined and accessible
# Add __all__ list if needed for explicit exports
__all__ = [
    'load_settings', 'save_settings', 'get_api_key', 'set_api_key',
    'get_mode', 'set_mode', 'get_permissions', 'update_permissions',
    'get_mcp_servers', 'update_mcp_servers'
]
```

### Phase 2: Session Management Refactoring

#### Files to Update: `grok/agent.py`
**Current Issues:**
- Line 68: Uses `prompt_toolkit.prompt()` instead of session instance
- Session instance created but not used consistently

**Solution:**
```python
# Replace direct prompt() calls with session.prompt()
# Line 68: Change from:
user_input = prompt_toolkit.prompt('> ')
# To:
user_input = session.prompt('> ')
```

### Phase 3: API Key Security Enhancement

#### Files to Update: `grok/agent.py`
**Current Issues:**
- Line 10: `openai.api_key = load_settings().get('api_key')` sets API key globally

**Solution:**
```python
# Remove global API key setting
# Line 10: Remove this line:
# openai.api_key = load_settings().get('api_key')

# Update call_api function to accept api_key parameter
def call_api(messages, tools=None, api_key=None):
    if api_key is None:
        api_key = load_settings().get('api_key')
    
    # Create client instance with API key
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )
    
    params = {
        "model": load_settings().get('model', 'grok-4'),
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
    }
    if tools:
        params["tools"] = tools
    
    response = client.chat.completions.create(**params)
    return response

# Update all call_api() calls to pass api_key parameter when needed
```

## Implementation Steps for Claude Code

### Step 1: Import Fixes
```
Task: Fix missing imports in agent.py and tools.py

Instructions:
1. Open grok/agent.py
2. Add import for get_permissions from config module at the top of the file
3. Add import for prompt from prompt_toolkit module at the top of the file
4. Open grok/tools.py
5. Add import for update_permissions from config module at the top of the file
6. Open grok/config.py
7. Add __all__ list with all exported functions to ensure proper module exports
8. Test all imports by running: python -c "from grok import agent, tools, config; print('All imports successful')"
```

### Step 2: Session Management Refactoring
```
Task: Replace direct prompt_toolkit calls with session instance usage

Instructions:
1. Open grok/agent.py
2. Locate line 68 where prompt_toolkit.prompt() is called directly
3. Replace with session.prompt() using the existing session instance
4. Verify session instance is properly initialized and accessible
5. Test prompt functionality by running the CLI and verifying user input works correctly
```

### Step 3: API Key Security Enhancement
```
Task: Move from global API key to per-request API key passing

Instructions:
1. Open grok/agent.py
2. Remove the global API key assignment on line 10
3. Modify call_api function to accept api_key parameter
4. Update call_api function to create OpenAI client instance with API key per request
5. Update all call_api() invocations to pass api_key when needed
6. Test API functionality by running a simple conversation to ensure API calls work correctly
```

## Testing Strategy

### Unit Tests
- Test all imports resolve correctly
- Test session.prompt() functionality
- Test API key passing mechanism

### Integration Tests
- Test complete conversation flow
- Test error handling for missing API key
- Test session management across multiple prompts

### Validation Criteria
- All modules import without ImportError
- Session prompts work correctly
- API calls execute successfully with per-request key handling
- No regression in existing functionality

## Risk Mitigation

### Potential Issues
- Breaking changes to existing API call patterns
- Session management conflicts
- Import circular dependencies

### Mitigation Strategies
- Incremental testing after each change
- Backup of original code before modifications
- Comprehensive testing of all interactive features

## Success Metrics
- Zero ImportError exceptions on module load
- Successful CLI startup and user interaction
- API calls execute without authentication errors
- All existing functionality preserved

## Next Steps
After completion of this task:
1. Task 002 (Security Framework) can safely proceed
2. Foundation is established for all subsequent development
3. Comprehensive testing framework can be built on stable foundation