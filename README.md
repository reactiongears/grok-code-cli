# Grok CLI

An open-source command-line interface for xAI's Grok LLM, designed to replicate the functionality and user experience of Claude Code CLI.

## 📋 Project Intention

This project aims to create a comprehensive, secure, and feature-rich CLI tool that provides Claude Code-like functionality using xAI's Grok API. The goal is to offer developers a powerful AI assistant for coding tasks, file operations, and development workflows with the same level of reliability and security as industry-leading tools.

**Key Objectives:**
- **Feature Parity**: Match Claude Code CLI's core functionality and user experience
- **Security First**: Implement robust security controls and input validation
- **Developer Experience**: Provide intuitive tools for common development workflows
- **Extensibility**: Support plugins and custom integrations
- **Cross-Platform**: Work seamlessly across Windows, macOS, and Linux


## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/grok-cli.git
cd grok-cli

# Install dependencies
pip install -e .

# Run the CLI
grok
```

### Configuration

```bash
# First time setup - get API key from https://console.x.ai/
grok
> /login

# Set operation mode
> /mode auto-complete  # or 'default' or 'planning'
```

## 🛠️ Current Features

- **Interactive CLI**: Conversational interface with Grok LLM
- **File Operations**: Basic file editing with VS Code diff preview
- **Command Execution**: Bash command execution with permission controls
- **Multiple Modes**: Default (interactive), auto-complete, and planning modes
- **MCP Integration**: Model Context Protocol server support
- **Configuration Management**: User and project-level settings
- **Custom Commands**: Extensible slash command system

## 📊 Development Roadmap

> 🚧 **UNDER CONSTRUCTION** 🚧
> 
> This project is actively under development. The following roadmap outlines our planned improvements to achieve full Claude Code CLI parity.

### Phase 1: Critical Fixes (High Priority)
- [x] **Fix Critical Import Dependencies and Session Management** ✅ **COMPLETED**
  - ✅ Fixed missing imports in agent.py and tools.py
  - ✅ Implemented proper session management and API key handling
  - ✅ All modules now load without errors
  - ✅ Added comprehensive TDD test suite (14 tests passing)

### Phase 2: Security & Stability (High Priority)
- [x] **Implement Comprehensive Security Framework** ✅ **COMPLETED**
  - ✅ Conducted security audit and vulnerability assessment
  - ✅ Added input sanitization and command validation framework
  - ✅ Implemented secure file operations and permission controls
  - ✅ Added rate limiting and enhanced security logging with audit trails
  - ✅ Created 32 comprehensive security tests (all passing)

### Phase 3: Core Features (High Priority)
- [x] **Implement File Operations Tool Suite** ✅ **COMPLETED**
  - ✅ Added read_file tool with line numbers, range selection, and encoding detection
  - ✅ Added list_files tool with recursive listing, pattern filtering, and metadata
  - ✅ Added find_files tool with regex matching and case sensitivity options
  - ✅ Added grep_files tool with content search, context lines, and binary exclusion
  - ✅ Implemented comprehensive error handling and security integration
  - ✅ Created 35 comprehensive TDD tests (all passing)

- [ ] **Implement Development Workflow Tools**
  - Add test execution with framework auto-detection
  - Create code linting with multiple linter support
  - Implement git operations (status, diff, commit, push)
  - Add dependency management for various package managers

- [ ] **Implement Network and System Tools**
  - Add HTTP request capabilities for API calls
  - Create system information and process management tools
  - Implement environment variable management

- [ ] **Implement Comprehensive Testing Framework**
  - Create unit, integration, and security test suites
  - Set up automated CI/CD pipeline
  - Add cross-platform compatibility validation

### Phase 4: Architecture (Medium Priority)
- [ ] **Implement Error Handling and Logging Framework**
  - Create centralized error handling with structured logging
  - Add retry mechanisms and user-friendly error messages
  - Implement comprehensive debugging capabilities

- [ ] **Improve Configuration Management System**
  - Add configuration validation with JSON schema
  - Implement migration system for version upgrades
  - Support environment-specific configurations

- [ ] **Design and Implement Plugin Architecture**
  - Create extensible plugin system for custom tools
  - Add plugin management CLI commands
  - Implement plugin sandboxing for security

- [ ] **Implement Monitoring and Metrics System**
  - Build monitoring dashboard for system health
  - Add automated alerting for critical issues
  - Track performance metrics and user analytics

- [ ] **Implement External Dependencies Health Check System**
  - Monitor xAI API connectivity and authentication
  - Validate system tools and VS Code availability
  - Add graceful degradation when dependencies are unavailable

### Phase 5: Advanced Features (Low Priority)
- [ ] **Implement Conversation Management System**
  - Add conversation persistence across sessions
  - Create conversation history with search capabilities
  - Implement context optimization and multi-session support

- [ ] **Implement Project Intelligence Features**
  - Add automatic project type detection
  - Create intelligent code recommendations
  - Implement project health monitoring

- [ ] **Implement Integration and Automation Features**
  - Add IDE integration support (VS Code, JetBrains)
  - Create CI/CD pipeline integrations
  - Implement webhook support for automation

- [ ] **Implement Phased Rollout and Deployment System**
  - Create feature flag system for controlled releases
  - Add early access program support
  - Implement automated release management

## 🔧 Usage Examples

### Basic Operations
```bash
# Interactive mode
grok
> Edit the README file to add installation instructions

# Single command mode
grok --print "Generate a Python function to calculate fibonacci numbers"

# Planning mode
grok --mode planning
> Implement user authentication system
```

### Slash Commands
```bash
# Authentication
> /login

# Mode switching
> /mode auto-complete

# Help and documentation
> /help

# Clear conversation
> /clear

# MCP server management
> /mcp add myserver /path/to/server
> /mcp list
```

## 🤝 Contributing

We welcome contributions from the community! This is an open-source project under the MIT license.

### Development Setup

```bash
# Clone and install for development
git clone https://github.com/your-username/grok-cli.git
cd grok-cli
pip install -e .

# Run tests
pytest

# Run linting
pylint grok/
```

### Contributing Guidelines

1. **Fork the repository** and create a feature branch
2. **Follow the existing code style** and conventions
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description of changes

### Reporting Issues

Please report bugs and feature requests through [GitHub Issues](https://github.com/your-username/grok-cli/issues).

## 📚 Documentation

- [CLAUDE.md](CLAUDE.md) - Guidance for Claude Code when working with this repository
- [PRD.md](PRD.md) - Product Requirements Document detailing planned improvements
- [tasks/](tasks/) - Detailed task breakdown and implementation plans

## 🏗️ Architecture

The project follows a modular architecture:

- **`grok/main.py`**: CLI entry point and argument parsing
- **`grok/agent.py`**: Core conversation loop and API integration
- **`grok/config.py`**: Configuration management and settings
- **`grok/tools.py`**: Tool definitions and execution handlers
- **`grok/slash_commands.py`**: Built-in command implementations

## 🔐 Security

Security is a top priority. We implement:

- Input sanitization and validation
- Command execution permissions
- Secure API key handling
- File system access controls
- Regular security audits

## 📈 Project Status

**Current Version**: 0.1.0 (Alpha)  
**Development Status**: Active Development  
**Stability**: Experimental - Not recommended for production use

**Recent Progress**:
- ✅ **Task 001 Complete**: Critical import dependencies and session management fixed
- ✅ **Task 002 Complete**: Comprehensive Security Framework implemented with full test coverage
- ✅ **Task 003 Complete**: File Operations Tool Suite implemented with 4 new tools and full security integration

## 🙏 Acknowledgments

- Inspired by Anthropic's Claude Code CLI
- Built for the xAI Grok ecosystem
- Thanks to all contributors and the open-source community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/grok-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/grok-cli/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/grok-cli/wiki)

---

**Note**: This project is not affiliated with Anthropic or xAI. It's an independent open-source initiative to create a Claude Code-like experience for Grok users.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Grok CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```