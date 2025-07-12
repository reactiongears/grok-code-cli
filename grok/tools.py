# grok/tools.py
import json
import subprocess
import tempfile
import os
import click
from .config import update_permissions
from .security import SecurityManager, SecurityError
from .file_operations import FileOperations

# Initialize security manager and file operations
security_manager = SecurityManager()
file_ops = FileOperations(security_manager)

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
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file content with optional line numbers and range selection",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to read"},
                    "show_line_numbers": {"type": "boolean", "description": "Show line numbers"},
                    "start_line": {"type": "integer", "description": "Starting line number"},
                    "max_lines": {"type": "integer", "description": "Maximum lines to read"}
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in directory with filtering options",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Directory path to list"},
                    "show_hidden": {"type": "boolean", "description": "Show hidden files"},
                    "recursive": {"type": "boolean", "description": "Recursive directory listing"},
                    "pattern": {"type": "string", "description": "File name pattern to match"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to filter"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Find files matching pattern in filename",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {"type": "string", "description": "Pattern to search for"},
                    "search_path": {"type": "string", "description": "Path to search in"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"},
                    "max_results": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["search_pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search for pattern within file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_pattern": {"type": "string", "description": "Pattern to search for"},
                    "search_path": {"type": "string", "description": "Path to search in"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search"},
                    "context_lines": {"type": "integer", "description": "Number of context lines"},
                    "file_types": {"type": "array", "items": {"type": "string"}, "description": "File extensions to search"},
                    "max_results": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["search_pattern"],
            },
        },
    }
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
    
    elif func_name == "read_file":
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to read file: {args.get('file_path', 'unknown')}"}
        
        result = file_ops.read_file(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result, indent=2)}
    
    elif func_name == "list_files":
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to list files in: {args.get('directory_path', '.')}"}
        
        result = file_ops.list_files(**args)
        # Convert FileInfo objects to dictionaries for JSON serialization
        if 'files' in result:
            result['files'] = [
                {
                    'path': f.path,
                    'name': f.name,
                    'size': f.size,
                    'size_formatted': f.size_formatted,
                    'is_directory': f.is_directory,
                    'is_binary': f.is_binary,
                    'modified_time': f.modified_time,
                    'permissions': f.permissions
                } for f in result['files']
            ]
        return {"tool_call_id": tool_call.id, "output": json.dumps(result, indent=2)}
    
    elif func_name == "find_files":
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to find files matching: {args.get('search_pattern', 'unknown')}"}
        
        result = file_ops.find_files(**args)
        return {"tool_call_id": tool_call.id, "output": json.dumps(result, indent=2)}
    
    elif func_name == "grep_files":
        if mode == "planning":
            return {"tool_call_id": tool_call.id, "output": f"Plan to search for pattern: {args.get('search_pattern', 'unknown')}"}
        
        result = file_ops.grep_files(**args)
        # Convert SearchResult objects to dictionaries for JSON serialization
        if 'results' in result:
            result['results'] = [
                {
                    'file_path': r.file_path,
                    'line_number': r.line_number,
                    'line_content': r.line_content,
                    'match_start': r.match_start,
                    'match_end': r.match_end,
                    'context_before': r.context_before,
                    'context_after': r.context_after
                } for r in result['results']
            ]
        return {"tool_call_id": tool_call.id, "output": json.dumps(result, indent=2)}