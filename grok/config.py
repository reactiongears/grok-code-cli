# grok/config.py
import os
import json

CONFIG_DIR = os.path.expanduser('~/.grok')
PROJECT_CONFIG = '.grok/settings.json'

os.makedirs(CONFIG_DIR, exist_ok=True)

# Explicit exports for better module interface
__all__ = [
    'load_settings', 'save_settings', 'get_api_key', 'set_api_key',
    'get_mode', 'set_mode', 'get_permissions', 'update_permissions',
    'get_mcp_servers', 'update_mcp_servers'
]

def load_settings():
    user_settings_path = os.path.join(CONFIG_DIR, 'settings.json')
    user_settings = {}
    if os.path.exists(user_settings_path):
        with open(user_settings_path, 'r') as f:
            user_settings = json.load(f)
    
    project_settings_path = os.path.join(os.getcwd(), PROJECT_CONFIG)
    project_settings = {}
    if os.path.exists(project_settings_path):
        with open(project_settings_path, 'r') as f:
            project_settings = json.load(f)
    
    # Merge: project overrides user
    settings = {**user_settings, **project_settings}
    return settings

def save_settings(settings, project=False):
    if project:
        path = os.path.join(os.getcwd(), PROJECT_CONFIG)
        os.makedirs(os.path.dirname(path), exist_ok=True)
    else:
        path = os.path.join(CONFIG_DIR, 'settings.json')
    with open(path, 'w') as f:
        json.dump(settings, f, indent=4)

def get_api_key():
    settings = load_settings()
    return settings.get('api_key')

def set_api_key(key):
    settings = load_settings()
    settings['api_key'] = key
    save_settings(settings)

def get_mode():
    settings = load_settings()
    return settings.get('mode', 'default')

def set_mode(mode):
    settings = load_settings()
    settings['mode'] = mode
    save_settings(settings)

def get_permissions():
    settings = load_settings()
    return settings.get('permissions', {'allow': [], 'deny': [], 'allowed_cmds': {}})

def update_permissions(permissions):
    settings = load_settings()
    settings['permissions'] = permissions
    save_settings(settings)

def get_mcp_servers():
    settings = load_settings()
    return settings.get('mcp_servers', {})

def update_mcp_servers(mcp_servers):
    settings = load_settings()
    settings['mcp_servers'] = mcp_servers
    save_settings(settings)