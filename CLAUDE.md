# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Grok CLI**, a Python-based interactive command-line interface for the Grok LLM API (xAI). The project creates a conversational AI assistant that can execute tools, edit files, and run bash commands with permission controls.

## Installation and Setup

```bash
# Install the package in development mode
pip install -e .

# Install dependencies
pip install openai>=1.0.0 click>=8.0.0 prompt_toolkit>=3.0.0

# Run the CLI
grok

# Or run directly
python -m grok.main
```

## Core Architecture

### Main Components

- **`grok/main.py`**: Entry point with CLI interface using Click. Handles command-line arguments and starts the agent loop.
- **`grok/agent.py`**: Core agent loop that manages conversation history, API calls to Grok, and tool execution. Contains the main interaction logic.
- **`grok/config.py`**: Configuration management for user/project settings, API keys, modes, permissions, and MCP servers.
- **`grok/tools.py`**: Tool definitions and handlers for file editing and bash command execution.
- **`grok/slash_commands.py`**: Built-in slash commands for authentication, mode switching, permissions, and MCP management.

### Key Features

- **Multiple Operation Modes**:
  - `default`: Interactive mode with user confirmation for file edits and commands
  - `auto-complete`: Automatic execution without confirmation
  - `planning`: Shows planned actions without execution

- **Permission System**: Granular control over command execution with allow/deny lists and per-project command approval

- **MCP Integration**: Support for Model Context Protocol servers with resource fetching and prompt execution

- **Configuration Hierarchy**: User-level (`~/.grok/settings.json`) and project-level (`.grok/settings.json`) settings

## Development Commands

```bash
# Run the CLI in development
python -m grok.main

# Run with specific mode
python -m grok.main --mode planning

# Run single command and exit
python -m grok.main --print "your prompt here"
```

## Built-in Slash Commands

- `/login` - Authenticate with xAI API (opens browser to get API key)
- `/init` - Initialize project with GROK.md documentation
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/mode [default/auto-complete/planning]` - Set operation mode
- `/permissions` - View/update command permissions
- `/mcp [add/list/remove/login]` - Manage MCP servers

## Configuration

### API Configuration
- API key stored in `~/.grok/settings.json` or `.grok/settings.json`
- Uses xAI API endpoint: `https://api.x.ai/v1`
- Default model: `grok-4`

### Permission Structure
```json
{
  "permissions": {
    "allow": ["safe_command1", "safe_command2"],
    "deny": ["dangerous_command"],
    "allowed_cmds": {
      "/path/to/project": ["project_specific_command"]
    }
  }
}
```

### MCP Server Configuration
```json
{
  "mcp_servers": {
    "server_name": {
      "transport": "stdio",
      "command": "server_executable",
      "args": [],
      "env": {}
    }
  }
}
```

## Tool System

The assistant can execute two main tool types:

1. **`edit_file`**: Edit files with VS Code diff preview in default mode
2. **`run_bash`**: Execute bash commands with permission controls

## Custom Commands

Create custom slash commands by adding `.md` files to:
- `.grok/commands/` (project-specific)
- `~/.grok/commands/` (user-global)

Use `$ARGUMENTS` placeholder for command arguments.

## MCP Resource Usage

Reference MCP resources in prompts using: `@server_name:resource_uri`
Execute MCP prompts using: `/mcp__server_name__prompt_name arguments`

## Important Notes

- The agent maintains conversation history across interactions
- File edits show diffs and require confirmation in default mode
- Commands are executed with permission checking
- Project initialization creates `GROK.md` documentation
- Settings cascade from user to project level (project overrides user)