# grok/agent.py
import openai
import re
import json
import subprocess
import os
from .config import load_settings, get_mode, get_mcp_servers, get_permissions
from .tools import TOOLS, handle_tool_call
from prompt_toolkit import prompt, PromptSession

# Initialize session for consistent prompt handling
session = PromptSession()

SYSTEM_PROMPT = "You are Grok 4, a helpful coding assistant. Use tools to edit code or run commands as needed."

def call_api(messages, tools=None, api_key=None):
    """
    Make API call with per-request API key passing for better security
    """
    if api_key is None:
        api_key = load_settings().get('api_key')
    
    # Create client instance with API key per request
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

def fetch_from_mcp(server, action_type, *args):
    mcp_servers = get_mcp_servers()
    if server not in mcp_servers:
        return f"Unknown MCP server: {server}"
    config = mcp_servers[server]
    if config.get('transport', 'stdio') == 'stdio':
        env = {**os.environ, **config.get('env', {})}
        p = subprocess.Popen([config['command']] + config.get('args', []), 
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                             env=env, text=True)
        if action_type == 'resource':
            msg = {"type": "fetch_resource", "uri": args[0]}
        elif action_type == 'prompt':
            msg = {"type": "execute_prompt", "prompt": args[0], "arguments": args[1]}
        else:
            return "Unknown action"
        p.stdin.write(json.dumps(msg) + '\n')
        p.stdin.close()
        output = p.stdout.read()
        error = p.stderr.read()
        p.wait()
        if error:
            return f"Error: {error}"
        try:
            res = json.loads(output)
            if 'error' in res:
                return f"Error: {res['error']}"
            return res.get('result', '')
        except:
            return output
    else:
        # TODO: Implement other transports
        return "Transport not implemented"

def agent_loop(initial_prompt=None):
    mode = get_mode()
    permissions = get_permissions()
    history = []
    if initial_prompt:
        history.append({"role": "user", "content": initial_prompt})
    
    while True:
        if not history or history[-1].get("role") == "assistant":
            user_input = session.prompt('> ')
            if user_input.startswith('/'):
                handle_slash_command(user_input, history)
                continue
            
            # Process MCP resources @server:uri
            resource_matches = re.findall(r'@(\w+):(\S+)', user_input)
            for server, uri in resource_matches:
                if mode == 'planning':
                    user_input = user_input.replace(f'@{server}:{uri}', f'[Plan to fetch resource {uri} from {server}]')
                else:
                    result = fetch_from_mcp(server, 'resource', uri)
                    user_input = user_input.replace(f'@{server}:{uri}', result)
            
            # If the entire input is /mcp__server__prompt args, handle it
            if user_input.startswith('/mcp__'):
                parts = user_input[6:].split('__', 1)
                server = parts[0]
                rest = parts[1].split(' ', 1)
                prompt_name = rest[0]
                args = rest[1] if len(rest) > 1 else ''
                if mode == 'planning':
                    history.append({"role": "system", "content": f"Plan to execute prompt {prompt_name} on {server} with args: {args}"})
                else:
                    result = fetch_from_mcp(server, 'prompt', prompt_name, args)
                    history.append({"role": "system", "content": result})
                continue  # Skip API call, wait for next input
            
            history.append({"role": "user", "content": user_input})
        
        response = call_api(history, tools=TOOLS if mode != 'planning' else None)
        message = response.choices[0].message
        
        if message.content:
            print(message.content)
        
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_result = handle_tool_call(tc, mode, permissions)
                history.append({"role": "tool", "content": json.dumps(tool_result)})
        
        history.append({"role": "assistant", "content": message.content or ""})