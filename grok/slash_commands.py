# grok/slash_commands.py
import os
import glob
import webbrowser
import json
import click
from .config import set_api_key, set_mode, update_permissions, load_settings, update_mcp_servers, get_mcp_servers
from .agent import call_api
from prompt_toolkit import print_formatted_text, HTML

def handle_slash_command(command, history):
    parts = command.split()
    cmd = parts[0][1:].lower()
    args = ' '.join(parts[1:])
    
    if cmd == 'login':
        webbrowser.open('https://console.x.ai/team/default/api-keys')
        key = click.prompt("Enter your xAI API key")
        set_api_key(key)
        print("API key saved.")
    
    elif cmd == 'init':
        file_list = '\n'.join(glob.glob('**/*', recursive=True, include_hidden=False))
        response = call_api([{"role": "user", "content": f"Analyze this project file list and document your understanding:\n{file_list}"}])
        with open('GROK.md', 'w') as f:
            f.write(response.choices[0].message.content)
        print("Project initialized, understanding documented in GROK.md")
    
    elif cmd == 'help':
        print_formatted_text(HTML('<b>Built-in Slash Commands:</b>'))
        print('/login - Authenticate with xAI API')
        print('/init - Initialize project with GROK.md')
        print('/help - Show this help')
        print('/clear - Clear conversation history')
        print('/mode [default/auto-complete/planning] - Set mode')
        print('/permissions - View/update permissions')
        print('/mcp [add/list/remove/login] - Manage MCP servers')
        # Add more as implemented
        
        # Custom commands
        custom_commands = get_custom_commands()
        if custom_commands:
            print_formatted_text(HTML('<b>Custom Commands:</b>'))
            for c in custom_commands:
                print(f'/{c}')
    
    elif cmd == 'clear':
        history.clear()
        print("Conversation cleared.")
    
    elif cmd == 'mode':
        if args in ['default', 'auto-complete', 'planning']:
            set_mode(args)
            print(f"Mode set to {args}")
        else:
            print("Invalid mode. Options: default, auto-complete, planning")
    
    elif cmd == 'permissions':
        permissions = get_permissions()
        print(json.dumps(permissions, indent=4))
        # Simple update, for demo
        if click.confirm("Update allow list?"):
            allow = click.prompt("Enter allow rules (comma separated)")
            permissions['allow'] = allow.split(',')
            update_permissions(permissions)
    
    elif cmd == 'mcp':
        subparts = args.split()
        if not subparts:
            print("MCP commands: add <name> <command>, list, remove <name>, login <name>")
            return
        subcmd = subparts[0].lower()
        if subcmd == 'add':
            name = subparts[1]
            command = ' '.join(subparts[2:])
            mcp_servers = get_mcp_servers()
            mcp_servers[name] = {'transport': 'stdio', 'command': command, 'args': [], 'env': {}}
            update_mcp_servers(mcp_servers)
            print(f"MCP server {name} added.")
        elif subcmd == 'list':
            mcp_servers = get_mcp_servers()
            for name, config in mcp_servers.items():
                print(f"{name}: {config['command']}")
        elif subcmd == 'remove':
            name = subparts[1]
            mcp_servers = get_mcp_servers()
            if name in mcp_servers:
                del mcp_servers[name]
                update_mcp_servers(mcp_servers)
                print(f"MCP server {name} removed.")
            else:
                print("Server not found.")
        elif subcmd == 'login':
            name = subparts[1]
            # Assume opens browser for OAuth
            webbrowser.open('https://example.com/oauth')  # Replace with actual if known
            token = click.prompt("Enter access token")
            mcp_servers = get_mcp_servers()
            if name in mcp_servers:
                mcp_servers[name]['env'] = mcp_servers[name].get('env', {})
                mcp_servers[name]['env']['ACCESS_TOKEN'] = token  # Generic
                update_mcp_servers(mcp_servers)
                print(f"Logged in to {name}.")
            else:
                print("Server not found.")
        else:
            print("Unknown MCP subcommand.")
    
    else:
        # Check custom
        custom_prompt = get_custom_prompt(cmd, args)
        if custom_prompt:
            history.append({"role": "user", "content": custom_prompt})
        else:
            print("Unknown command. Use /help")

def get_custom_commands():
    project_cmds = glob.glob('.grok/commands/*.md')
    user_cmds = glob.glob(os.path.expanduser('~/.grok/commands/*.md'))
    commands = [os.path.basename(p).replace('.md', '') for p in project_cmds + user_cmds]
    return commands

def get_custom_prompt(cmd, args):
    paths = [
        f'.grok/commands/{cmd}.md',
        os.path.expanduser(f'~/.grok/commands/{cmd}.md')
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                prompt = f.read().replace('$ARGUMENTS', args)
            return prompt
    return None