# NextEleven Terminal Agent

> **AI-powered terminal assistant for macOS** that brings intelligent command generation, error explanation, and safe execution directly into your Terminal.app. Powered by **NextEleven's eleven AI**, this tool provides Claude-like terminal integration with prefix-triggered AI assistance.

[![Production Ready](https://img.shields.io/badge/status-production--ready-success)](https://github.com/yourusername/next-eleven-terminal)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![macOS 14+](https://img.shields.io/badge/macOS-14+-lightgrey.svg)](https://www.apple.com/macos/)

---

## 🚀 Quick Start

### Install in 30 Seconds

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/next-eleven-terminal/main/install.sh | bash
```

Then restart your terminal and try:

```bash
NextEleven AI: list files in current directory
```

Or start interactive mode:

```bash
grok
```

---

## ✨ What is This?

**NextEleven Terminal Agent** is a production-ready CLI tool that seamlessly integrates **NextEleven's eleven AI** into your macOS terminal (zsh shell). Instead of switching between your terminal and a browser or separate AI tool, you can now get AI assistance directly in your command line.

**Think of it as:** Having an AI pair programmer in your terminal that helps you:
- 🎯 Generate shell commands from natural language
- 🔍 Explain errors and suggest fixes
- 📝 Provide safe command execution with previews
- 💬 Maintain context across conversations
- 🛠️ Use tools to interact with your system

---

## 🎯 Key Features

### 🚀 Two Usage Modes

**1. Prefix Mode (Quick Queries)**
```bash
NextEleven AI: find all Python files modified today
```

**2. Interactive Mode (Chat Sessions)**
```bash
grok
# Then have a conversation with eleven
```

### 🛡️ Enterprise-Grade Security

- ✅ **macOS Keychain Integration**: API keys stored encrypted, never in plain text
- ✅ **Command Validation**: All commands validated before execution
- ✅ **Dangerous Command Detection**: Automatically flags risky operations
- ✅ **User Confirmation**: Every command requires explicit `y/n` approval
- ✅ **Dry-run Previews**: See exactly what will execute before running
- ✅ **Optional Logging**: Control what gets logged with `--no-log` flag
- ✅ **No Auto-execution**: Zero unsafe automatic command execution

### 💬 Conversational AI

- **Context Awareness**: Knows your current directory, git status, and project structure
- **History Persistence**: Remembers previous conversations across sessions
- **Topic Detection**: Automatically detects new conversation topics
- **Smart Compaction**: Summarizes long conversations to manage tokens

### 🛠️ Tool Calling System

**eleven** can use tools to interact with your system:

- **Bash**: Execute shell commands safely
- **View**: Read file contents
- **Edit**: Edit files with vim
- **Write**: Create new files
- **LS**: List directory contents
- **Glob**: Pattern-based file search
- **Grep**: Search text in files

### ⚡ Production Features

- **Real-Time Streaming**: See responses stream in real-time
- **Response Caching**: Reduces API calls with intelligent caching
- **Connection Pooling**: Optimized HTTP client performance
- **Retry Logic**: Automatic retry with exponential backoff
- **Health Checks**: System health monitoring
- **File Locking**: Safe concurrent access
- **Corruption Detection**: Automatic data validation

---

## 📦 Installation

### Prerequisites

- macOS Sonoma 14+ (or later)
- zsh as your default shell
- Python 3.12+ installed
- Homebrew (for dependencies)

### One-Click Install

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/next-eleven-terminal/main/install.sh | bash
```

### What Gets Installed

The installer automatically:
- ✅ Verifies macOS Sonoma 14+ compatibility
- ✅ Checks zsh as default shell
- ✅ Validates Python 3.12+ installation
- ✅ Ensures Homebrew is installed
- ✅ Installs fzf if missing
- ✅ Installs Python dependencies (httpx, termcolor)
- ✅ Prompts for NextEleven API key
- ✅ Stores API key securely in macOS Keychain
- ✅ Copies files to `~/.grok_terminal/`
- ✅ Adds source line to `~/.zshrc`

### After Installation

Restart your terminal or run:
```bash
source ~/.zshrc
```

### Verify Installation

```bash
# Test prefix mode
NextEleven AI: hello

# Test interactive mode
grok --help
```

---

## 📖 Usage

### Prefix Mode (Quick Queries)

Type `NextEleven AI:` followed by your query:

```bash
# Basic queries
NextEleven AI: list files in current directory
NextEleven AI: explain git merge vs rebase
NextEleven AI: find files larger than 100MB

# With flags
NextEleven AI: list processes --no-log          # Don't log this query
NextEleven AI: remove old logs --force          # Allow dangerous command
```

### Interactive Mode (Chat Sessions)

Start a conversation:

```bash
grok
```

**Interactive Features:**
- Chat-like interface
- Slash commands (`/help`, `/init`, `/clear`, `/hooks`)
- Context maintained across queries
- History automatically saved

**Slash Commands:**
- `/help` - Show available commands
- `/init` - Generate ELEVEN.md project file
- `/clear` - Clear conversation history
- `/hooks` - Show hooks directory location
- `exit` - End session

### Example Session

```bash
$ grok
Start eleven Terminal Agent session?
1. Yes
2. Decline
> 1

eleven session started. Type queries; /help for commands; 'exit' to quit.

You: help me understand this git error
eleven: [Streams explanation in real-time...]

You: can you fix it?
eleven: [Suggests commands with preview...]

You: exit
Session ended.
```

---

## 🎨 Features in Detail

### Safe Command Execution

Every command goes through multiple safety checks:

1. **Preview**: See what will execute
2. **Risk Classification**: SAFE/CAUTION/DANGEROUS
3. **User Confirmation**: Explicit `y/n` approval required
4. **Command Editing**: Option to edit before execution
5. **Execution**: Runs only after approval

**Example:**
```
Preview: Would run in /Users/you/project
Command: ls -la
Risk: SAFE

Execute? [y/n/e(dit)]: y
✓ Command completed.
```

### Context Awareness

**eleven** automatically knows:
- Current working directory
- Git status (if in a git repo)
- Directory tree structure
- Previous conversation history

This context helps provide more relevant suggestions.

### Tool Calling

**eleven** can use tools to interact with your system:

```
You: read the README file
eleven: [Uses View tool to read README.md]

You: create a backup script
eleven: [Uses Write tool to create backup.sh]

You: find all Python files
eleven: [Uses Glob tool with pattern *.py]
```

### History & Memory

- **Automatic Saving**: Conversations saved to `~/.grok_terminal_history.json`
- **Smart Compaction**: Long conversations automatically summarized
- **Context Preservation**: Previous queries remembered across sessions
- **Todos Persistence**: Mentions of "todo" automatically saved

---

## ⚙️ Configuration

### Configuration File

Create `~/.grok_terminal_config.json`:

```json
{
  "model": "grok-beta",
  "temperature": 0.1,
  "max_tokens": 2048,
  "auto_log": true,
  "dangerous_commands_require_flag": true,
  "cache_enabled": true,
  "cache_size": 100,
  "cache_ttl": 300,
  "max_retries": 3,
  "retry_base_delay": 1.0,
  "retry_max_delay": 60.0,
  "health_check_enabled": true
}
```

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `grok-beta` | AI model to use |
| `temperature` | float | `0.1` | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | `2048` | Maximum response tokens |
| `auto_log` | bool | `true` | Automatically log interactions |
| `dangerous_commands_require_flag` | bool | `true` | Require --force for dangerous commands |
| `cache_enabled` | bool | `true` | Enable response caching |
| `cache_size` | int | `100` | Maximum cache entries |
| `cache_ttl` | int | `300` | Cache TTL in seconds (5 minutes) |
| `max_retries` | int | `3` | Maximum API retry attempts |
| `retry_base_delay` | float | `1.0` | Base retry delay in seconds |
| `retry_max_delay` | float | `60.0` | Maximum retry delay in seconds |
| `health_check_enabled` | bool | `true` | Enable health checks |

---

## 🔧 Advanced Features

### Hooks System

Create custom scripts to run before/after tool execution:

**Pre-hook:** `~/.grok_terminal/hooks/PreToolUse.sh`
```bash
#!/bin/bash
# Runs before tool execution
# Receives JSON via stdin: {"tool": "Bash", "params": {...}}
# Return 0 to allow, non-zero to block
exit 0
```

**Post-hook:** `~/.grok_terminal/hooks/PostToolUse.sh`
```bash
#!/bin/bash
# Runs after tool execution
# Receives JSON via stdin: {"tool": "Bash", "result": "..."}
exit 0
```

### Custom System Prompts

Modify the system prompt in `grok_agent.py` to customize **eleven's** behavior:

```python
def get_system_prompt(cwd: str, git_status: str, dir_tree: str) -> str:
    return f"""Your custom instructions here...
    Current dir: {cwd}
    Be specific about how you want eleven to respond."""
```

### Custom Prefix

Edit `~/.grok_terminal/grok.zsh`:

```zsh
GROK_PREFIX="Your Custom Prefix:"
```

Then restart your terminal.

---

## 🛡️ Security

### Security Features

- ✅ **API Key Storage**: Encrypted in macOS Keychain
- ✅ **Command Validation**: All commands validated before execution
- ✅ **Dangerous Command Detection**: Automatic flagging of risky operations
- ✅ **User Confirmation**: All commands require explicit approval
- ✅ **Dry-run Previews**: See what will execute before running
- ✅ **Optional Logging**: Control what gets logged
- ✅ **No Auto-execution**: Zero unsafe automatic execution
- ✅ **File Locking**: Safe concurrent access
- ✅ **Input Sanitization**: All inputs sanitized
- ✅ **Permission Enforcement**: Secure file permissions (600)

### Dangerous Command Detection

The following patterns are automatically flagged:
- `rm -rf` (recursive deletion)
- `sudo` (privilege escalation)
- `kill -9` (force kill)
- `mkfs` (filesystem creation)
- `dd if=` (disk operations)
- `chmod 777` (permissive permissions)
- `> /dev/` (device redirection)
- `format` (formatting operations)
- `fdisk` (partition operations)

### Security Best Practices

1. **Always review commands** before executing
2. **Use `--force` flag** only when absolutely necessary
3. **Keep API key secure** - never commit to git or share publicly
4. **Review logs periodically**: `tail -f ~/.grok_terminal/grok.log`
5. **Use `--no-log`** for sensitive queries
6. **Verify command context** - check the "Would run in" directory

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"API key not found"** | Run `install.sh` or manually add: `security add-generic-password -s grok-terminal -a xai-api-key -w YOUR_NEXTELEVEN_KEY` |
| **"Python 3.12+ required"** | Install via Homebrew: `brew install python@3.12` |
| **"fzf not found"** | Install via Homebrew: `brew install fzf` |
| **"httpx not found"** | Install via pip: `pip3 install --user httpx termcolor` |
| **Commands not executing** | Verify `grok.zsh` is sourced: `grep grok ~/.zshrc` |
| **Streaming not working** | Check Python/httpx: `python3 --version && pip3 show httpx` |
| **Rate limit errors** | Wait between requests or upgrade NextEleven API plan |
| **Keychain access denied** | Grant Terminal.app access in System Settings > Privacy & Security |
| **Prefix not recognized** | Restart terminal or run `source ~/.zshrc` |

### Debug Mode

**View Logs:**
```bash
tail -f ~/.grok_terminal/grok.log
```

**Check Configuration:**
```bash
cat ~/.grok_terminal_config.json
```

**View History:**
```bash
cat ~/.grok_terminal_history.json
```

**Test Installation:**
```bash
python3 ~/.grok_terminal/grok_agent.py --help
```

---

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Comprehensive guide to using NextEleven Terminal Agent
- **[Production Quality Report](PRODUCTION_QUALITY_REPORT.md)** - Production-readiness assessment
- **[White-Label Report](WHITELABEL_REPORT.md)** - Branding information

---

## 🏗️ Architecture

### Component Overview

```
User Input
    │
    ├─→ Prefix Mode: "NextEleven AI: <query>"
    │   └─→ grok.zsh (Zsh Plugin)
    │       └─→ grok_agent.py (Python Agent)
    │           └─→ NextEleven API
    │
    └─→ Interactive Mode: "grok"
        └─→ grok_agent.py (Python Agent)
            └─→ NextEleven API
                └─→ Tool Calling
                    ├─→ Bash, View, Edit, Write
                    ├─→ LS, Glob, Grep
                    └─→ Hooks (Pre/Post)
```

### Key Components

**grok.zsh (Zsh Plugin)**
- Prefix detection and parsing
- Command execution wrapper
- fzf integration for command selection

**grok_agent.py (Python Agent)**
- API client with streaming support
- Tool calling system
- History and context management
- Security validation

**security_utils.py**
- Input sanitization
- Command validation
- Safe execution

---

## 📊 Technical Specifications

- **Platform**: macOS Sonoma 14+
- **Shell**: zsh (default macOS shell)
- **Python**: 3.12+ (required)
- **Dependencies**: 
  - Homebrew (for fzf)
  - httpx (Python async HTTP client)
  - termcolor (for colored output)
  - fzf (fuzzy finder)
- **API**: NextEleven API (`https://api.x.ai/v1/chat/completions`)
- **Model**: `grok-beta` (configurable)
- **Authentication**: macOS Keychain (encrypted storage)
- **Code Size**: ~1,100 LOC total (Python: ~900, Zsh: ~200)

---

## 🎯 Use Cases

### Development
- Generate shell commands from natural language
- Explain git operations and workflows
- Debug terminal errors
- Navigate codebases
- Generate scripts

### System Administration
- Find and manage files
- Monitor system resources
- Clean up disk space
- Manage processes
- System diagnostics

### Learning
- Understand complex commands
- Learn shell scripting
- Explore system internals
- Command reference

---

## 🤝 Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows existing style
- Security best practices are maintained
- Documentation is updated
- Changes are backward compatible

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for macOS Terminal.app integration
- Powered by **NextEleven's eleven AI**
- Inspired by Claude's terminal integration features
- Uses fzf for enhanced command selection UX

---

## 📞 Support

For issues, questions, or feature requests:
1. Check the [User Guide](USER_GUIDE.md)
2. Review the [Troubleshooting](#-troubleshooting) section
3. Check logs: `tail -f ~/.grok_terminal/grok.log`
4. Open an issue on GitHub

---

**Made with ❤️ for the macOS terminal community**

**Powered by NextEleven's eleven AI**

---

## Quick Reference

### Commands

```bash
# Prefix mode
NextEleven AI: <your query>

# Interactive mode
grok

# With flags
NextEleven AI: <query> --no-log --force
grok --force --no-log
```

### Slash Commands (Interactive Mode)

```
/help    # Show help
/init    # Generate ELEVEN.md
/clear   # Clear history
/hooks   # Show hooks directory
exit     # Exit session
```

### File Locations

- `~/.grok_terminal/` - Installation directory
- `~/.grok_terminal_history.json` - Conversation history
- `~/.grok_terminal/todos.json` - Saved todos
- `~/.grok_terminal_config.json` - Configuration
- `~/.grok_terminal/grok.log` - Application logs

---

**Ready to get started?** Run `grok` or type `NextEleven AI: help`!
