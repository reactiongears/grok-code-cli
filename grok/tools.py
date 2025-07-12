# grok/tools.py
import json
import subprocess
import tempfile
import os
import click
from .config import update_permissions
from .security import SecurityManager, SecurityError

# Initialize security manager
security_manager = SecurityManager()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file with new content. Use this for code changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"},
                    "content": {"type": "string", "description": "New full content of the file"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Run a bash command in the terminal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "The bash command to run"},
                },
                "required": ["cmd"],
            },
        },
    },
    # Add more tools like read_file, etc., if needed
]

def handle_tool_call(tool_call, mode, permissions):
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    if func_name == "edit_file":
        path = args['path']
        content = args['content']
        
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to edit {path} with new content."}
        
        # Security validation for file operations
        if not security_manager.validate_file_operation(path, 'write'):
            security_manager.log_security_event('file_access_denied', {
                'path': path, 'operation': 'write', 'tool': 'edit_file'
            })
            return {"tool_call_id": tool_call.id, "output": "File access denied for security reasons."}
        
        # Sanitize content
        try:
            sanitized_content = security_manager.validate_input(content)
        except SecurityError as e:
            security_manager.log_security_event('input_validation_failed', {
                'error': str(e), 'tool': 'edit_file'
            })
            return {"tool_call_id": tool_call.id, "output": f"Input validation failed: {e}"}
        
        full_path = os.path.join(os.getcwd(), path)
        if not os.path.exists(full_path):
            return {"tool_call_id": tool_call.id, "output": "File does not exist."}
        
        original_content = open(full_path).read()
        
        if mode == "default":
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as old_file, tempfile.NamedTemporaryFile(mode='w', delete=False) as new_file:
                old_file.write(original_content)
                new_file.write(sanitized_content)
                old_file.flush()
                new_file.flush()
                subprocess.call(["code", "--diff", "--wait", old_file.name, new_file.name])
            accept = click.prompt("Accept changes? (y/n)", type=str).lower()
            if accept == 'y':
                with open(full_path, 'w') as f:
                    f.write(sanitized_content)
                return {"tool_call_id": tool_call.id, "output": "Edit applied."}
            else:
                return {"tool_call_id": tool_call.id, "output": "Edit rejected."}
        elif mode == "auto-complete":
            with open(full_path, 'w') as f:
                f.write(sanitized_content)
            return {"tool_call_id": tool_call.id, "output": "Edit applied automatically."}
    
    elif func_name == "run_bash":
        cmd = args['cmd']
        
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to run bash: {cmd}"}
        
        # Security validation for commands
        if not security_manager.validate_command(cmd):
            security_manager.log_security_event('command_blocked', {
                'command': cmd, 'reason': 'dangerous_command', 'tool': 'run_bash'
            })
            return {"tool_call_id": tool_call.id, "output": "Command blocked for security reasons."}
        
        # Check permissions
        project_dir = os.getcwd()
        allowed_cmds = permissions.get('allowed_cmds', {}).get(project_dir, [])
        if cmd in permissions['deny']:
            return {"tool_call_id": tool_call.id, "output": "Command denied by permissions."}
        if cmd in permissions['allow'] or cmd in allowed_cmds:
            try:
                output = subprocess.check_output(cmd, shell=True, text=True)
                return {"tool_call_id": tool_call.id, "output": output}
            except Exception as e:
                return {"tool_call_id": tool_call.id, "output": str(e)}
        else:
            choice = click.prompt(f"Run command '{cmd}'? (y/ya [yes and don't ask again for this type in project]/n)", type=str).lower()
            if choice == 'y':
                try:
                    output = subprocess.check_output(cmd, shell=True, text=True)
                    return {"tool_call_id": tool_call.id, "output": output}
                except Exception as e:
                    return {"tool_call_id": tool_call.id, "output": str(e)}
            elif choice == 'ya':
                permissions['allowed_cmds'] = permissions.get('allowed_cmds', {})
                permissions['allowed_cmds'][project_dir] = permissions['allowed_cmds'].get(project_dir, []) + [cmd]
                update_permissions(permissions)
                try:
                    output = subprocess.check_output(cmd, shell=True, text=True)
                    return {"tool_call_id": tool_call.id, "output": output}
                except Exception as e:
                    return {"tool_call_id": tool_call.id, "output": str(e)}
            else:
                return {"tool_call_id": tool_call.id, "output": "Command interrupted."}