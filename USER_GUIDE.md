# NextEleven Terminal Agent - User Guide
## Complete Guide to Using eleven AI in Your Terminal
**Version:** 1.0  
**Last Updated:** January 2026

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Usage Modes](#usage-modes)
5. [Commands & Features](#commands--features)
6. [Interactive Mode](#interactive-mode)
7. [Prefix Mode](#prefix-mode)
8. [Tool Calling](#tool-calling)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Usage](#advanced-usage)
12. [Security & Best Practices](#security--best-practices)

---

## Introduction

**NextEleven Terminal Agent** brings the power of **eleven AI** directly into your macOS terminal. It's like having an AI pair programmer that understands your codebase, helps with commands, and provides intelligent assistance—all without leaving your terminal.

### What Can eleven Do?

- 🎯 **Generate Commands**: Convert natural language to shell commands
- 🔍 **Explain Errors**: Understand and fix terminal errors
- 📝 **Code Assistance**: Help with scripts, git operations, and more
- 🛠️ **Tool Integration**: Execute commands, view/edit files, search code
- 💬 **Conversational**: Maintains context across multiple queries
- 🎨 **Interactive**: Chat-like interface for complex tasks

---

## Installation

### Prerequisites

- macOS Sonoma 14+ (or later)
- zsh as your default shell
- Python 3.12+ installed
- Homebrew (for dependencies)

### Quick Install

```bash
# One-click installation
curl -fsSL https://raw.githubusercontent.com/yourusername/next-eleven-terminal/main/install.sh | bash
```

Or if you've cloned the repository:

```bash
chmod +x install.sh
./install.sh
```

### What the Installer Does

1. ✅ Verifies macOS version (14+)
2. ✅ Checks zsh shell
3. ✅ Validates Python 3.12+
4. ✅ Installs Homebrew (if needed)
5. ✅ Installs fzf (fuzzy finder)
6. ✅ Installs Python dependencies (httpx, termcolor)
7. ✅ Prompts for NextEleven API key
8. ✅ Stores API key securely in macOS Keychain
9. ✅ Copies files to `~/.grok_terminal/`
10. ✅ Adds to `~/.zshrc`

### After Installation

Restart your terminal or run:
```bash
source ~/.zshrc
```

### Verify Installation

```bash
# Test the command
grok --help

# Test prefix mode
NextEleven AI: hello
```

---

## Quick Start

### Your First Query

**Prefix Mode (Quick Queries):**
```bash
NextEleven AI: list files in current directory
```

**Interactive Mode (Chat-like):**
```bash
grok
# Then type your queries
```

### What You'll See

1. **eleven** processes your query
2. Response streams in real-time
3. Commands are suggested (if applicable)
4. You confirm before execution
5. Results are displayed

---

## Usage Modes

### 1. Prefix Mode (Quick Queries)

Type `NextEleven AI:` followed by your query anywhere in the terminal.

**Examples:**
```bash
NextEleven AI: list all Python files
NextEleven AI: explain git merge vs rebase
NextEleven AI: find large files over 100MB
```

**With Flags:**
```bash
NextEleven AI: list processes --no-log          # Don't log this query
NextEleven AI: remove old logs --force          # Allow dangerous command
```

**Best For:**
- Quick questions
- Single command generation
- Quick explanations
- Fast lookups

---

### 2. Interactive Mode (Chat Sessions)

Start a conversation session with **eleven**:

```bash
grok
```

**What Happens:**
1. You'll see: "Start eleven Terminal Agent session?"
2. Type `1` to start, `2` to decline
3. Enter interactive chat mode
4. Type queries, use slash commands
5. Type `exit` to end session

**Slash Commands:**
- `/help` - Show available commands
- `/init` - Generate ELEVEN.md project file
- `/clear` - Clear conversation history
- `/hooks` - Show hooks directory location

**Best For:**
- Multi-turn conversations
- Complex tasks requiring context
- Code generation and editing
- Extended debugging sessions

---

## Commands & Features

### Basic Commands

#### List Files
```bash
NextEleven AI: list files in current directory
```
**Output:** Suggests `ls -la` with preview and confirmation

#### Explain Commands
```bash
NextEleven AI: explain what this does: find . -name "*.py" -exec rm {} \;
```
**Output:** Detailed explanation of the command

#### Generate Scripts
```bash
NextEleven AI: create a backup script for my home directory
```
**Output:** Complete shell script with comments

#### Git Operations
```bash
NextEleven AI: show git commands to clean up old branches
NextEleven AI: explain git rebase vs merge
```

#### Find Files
```bash
NextEleven AI: find all Python files modified in last 7 days
NextEleven AI: find files larger than 100MB
```

---

### Advanced Features

#### Tool Calling

**eleven** can use tools to interact with your system:

- **Bash**: Execute shell commands
- **View**: Read file contents
- **Edit**: Edit files with vim
- **Write**: Create new files
- **LS**: List directory contents
- **Glob**: Pattern-based file search
- **Grep**: Search text in files

**Example:**
```
You: read the README file
eleven: [Uses View tool to read README.md]
```

#### Context Awareness

**eleven** automatically knows:
- Current working directory
- Git status (if in a git repo)
- Directory structure
- Previous conversation history

#### History Persistence

Conversations are saved automatically:
- Location: `~/.grok_terminal_history.json`
- Last 40 messages kept
- Automatically compacted when too long

#### Topic Detection

**eleven** detects when you start a new topic and can organize conversations accordingly.

---

## Interactive Mode

### Starting Interactive Mode

```bash
grok
```

### Interactive Session Flow

1. **Start Prompt:**
   ```
   Start eleven Terminal Agent session?
   This allows API calls, file operations, and commands.
   1. Yes
   2. Decline
   > 
   ```

2. **Quota Check:**
   - Lightweight API call to verify access
   - Continues even if check fails

3. **History Summarization:**
   - If previous history exists, it's summarized
   - Keeps context without token bloat

4. **Chat Loop:**
   ```
   eleven session started. Type queries; /help for commands; 'exit' to quit.
   You: [your query]
   eleven: [streaming response]
   ```

### Slash Commands

#### `/help`
Shows available commands:
```
Commands:
  /init  - Generate ELEVEN.md with project instructions/tools
  /clear - Reset conversation history
  /hooks - Configure hooks in ~/.grok_terminal/hooks/
```

#### `/init`
Generates `ELEVEN.md` file with:
- Project instructions
- Available tools
- Custom guidelines

#### `/clear`
Clears conversation history (keeps system prompt)

#### `/hooks`
Shows hooks directory location for custom scripts

### Exiting Interactive Mode

- Type `exit` to end session
- Press `Ctrl+C` to interrupt
- Press `Ctrl+D` (EOF) to exit

---

## Prefix Mode

### Basic Usage

```bash
NextEleven AI: <your query>
```

### With Flags

```bash
# Disable logging
NextEleven AI: list processes --no-log

# Force dangerous commands
NextEleven AI: remove old logs --force

# Combine flags
NextEleven AI: cleanup temp files --force --no-log
```

### Command Execution Flow

1. **Query Processing:**
   - Your query is sent to NextEleven API
   - Response streams in real-time

2. **Command Extraction:**
   - If commands are suggested, they're extracted
   - Risk level is classified (SAFE/CAUTION/DANGEROUS)

3. **Preview:**
   ```
   Preview: Would run in /Users/you/project
   Command: ls -la
   Risk: SAFE
   ```

4. **Confirmation:**
   ```
   Execute? [y/n/e(dit)]: 
   ```
   - `y` - Execute command
   - `n` - Skip command
   - `e` - Edit command in vim

5. **Execution:**
   - Command runs in the specified directory
   - Results displayed
   - Success/failure indicated

---

## Tool Calling

**eleven** can use tools to interact with your system. Tools are called automatically when needed.

### Available Tools

#### Bash Tool
Executes shell commands safely.

**Example:**
```
You: run git status
eleven: [Uses Bash tool]
     On branch main
     Your branch is up to date...
```

#### View Tool
Reads file contents.

**Example:**
```
You: show me the README file
eleven: [Uses View tool to read README.md]
```

#### Edit Tool
Opens file in vim for editing.

**Example:**
```
You: edit the config file
eleven: [Uses Edit tool to open ~/.grok_terminal_config.json]
```

#### Write Tool
Creates new files.

**Example:**
```
You: create a new script called backup.sh
eleven: [Uses Write tool to create backup.sh]
```

#### LS Tool
Lists directory contents.

**Example:**
```
You: list files in the src directory
eleven: [Uses LS tool]
```

#### Glob Tool
Finds files matching patterns.

**Example:**
```
You: find all Python files
eleven: [Uses Glob tool with pattern *.py]
```

#### Grep Tool
Searches text in files.

**Example:**
```
You: search for "TODO" in all files
eleven: [Uses Grep tool]
```

### Tool Execution Flow

1. **eleven** decides which tool to use
2. **Pre-hook** runs (if `PreToolUse.sh` exists)
3. **Permission check** (for dangerous operations)
4. **Tool executes**
5. **Post-hook** runs (if `PostToolUse.sh` exists)
6. **Results** returned to conversation

---

## Configuration

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

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `grok-beta` | AI model to use |
| `temperature` | float | `0.1` | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | `2048` | Maximum response tokens |
| `auto_log` | bool | `true` | Automatically log interactions |
| `dangerous_commands_require_flag` | bool | `true` | Require --force for dangerous commands |
| `cache_enabled` | bool | `true` | Enable response caching |
| `cache_size` | int | `100` | Maximum cache entries |
| `cache_ttl` | int | `300` | Cache TTL in seconds |
| `max_retries` | int | `3` | Maximum API retry attempts |
| `retry_base_delay` | float | `1.0` | Base retry delay in seconds |
| `retry_max_delay` | float | `60.0` | Maximum retry delay in seconds |
| `health_check_enabled` | bool | `true` | Enable health checks |

### Customizing the Prefix

Edit `~/.grok_terminal/grok.zsh`:

```zsh
GROK_PREFIX="Your Custom Prefix:"
```

Then restart your terminal or run `source ~/.zshrc`.

---

## Troubleshooting

### Common Issues

#### "API key not found"

**Solution:**
```bash
# Run installer again
./install.sh

# Or manually add key
security add-generic-password -s grok-terminal -a xai-api-key -w YOUR_NEXTELEVEN_API_KEY
```

#### "Python 3.12+ required"

**Solution:**
```bash
brew install python@3.12
```

#### "fzf not found"

**Solution:**
```bash
brew install fzf
```

#### "Commands not executing"

**Solution:**
```bash
# Verify zsh plugin is loaded
grep grok ~/.zshrc

# Reload zsh
source ~/.zshrc
```

#### "Rate limit errors"

**Solution:**
- Wait between requests
- Upgrade your NextEleven API plan
- Check your API quota

#### "Keychain access denied"

**Solution:**
1. Open System Settings
2. Go to Privacy & Security
3. Grant Terminal.app access to Keychain

#### "Prefix not recognized"

**Solution:**
```bash
# Restart terminal or reload zsh
source ~/.zshrc

# Verify function exists
type NextEleven
```

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

**Test API Connection:**
```bash
python3 ~/.grok_terminal/grok_agent.py --help
```

---

## Advanced Usage

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

Modify the system prompt in `grok_agent.py`:

```python
def get_system_prompt(cwd: str, git_status: str, dir_tree: str) -> str:
    return f"""Your custom prompt here...
    Current dir: {cwd}
    Be specific about how you want eleven to respond."""
```

### Environment Context

**eleven** automatically includes:
- Current working directory
- Git status (if in git repo)
- Directory tree structure

This context helps **eleven** provide more relevant suggestions.

### History Management

**Automatic Compaction:**
- When history exceeds 20 messages, it's automatically summarized
- Keeps context without token bloat
- Original messages preserved in `~/.grok_terminal_history.json`

**Manual History:**
```bash
# View history
cat ~/.grok_terminal_history.json

# Clear history (in interactive mode)
/clear
```

### Todos Persistence

When you mention "todo" in your query, **eleven** automatically saves it:

**Location:** `~/.grok_terminal/todos.json`

**Format:**
```json
{
  "2026-01-15T10:30:00": "Implement feature X",
  "2026-01-15T11:00:00": "Fix bug Y"
}
```

---

## Security & Best Practices

### Security Features

✅ **API Key Storage**: Encrypted in macOS Keychain  
✅ **Command Validation**: All commands validated before execution  
✅ **Dangerous Command Detection**: Automatic flagging of risky operations  
✅ **User Confirmation**: All commands require explicit approval  
✅ **Dry-run Previews**: See what will execute before running  
✅ **Optional Logging**: Control what gets logged  
✅ **No Auto-execution**: Zero unsafe automatic execution  

### Dangerous Commands

These patterns are automatically flagged:
- `rm -rf` (recursive deletion)
- `sudo` (privilege escalation)
- `kill -9` (force kill)
- `mkfs` (filesystem creation)
- `dd if=` (disk operations)
- `chmod 777` (permissive permissions)
- `> /dev/` (device redirection)
- `format` (formatting operations)
- `fdisk` (partition operations)

### Best Practices

1. **Always Review Commands**
   - Check the preview before executing
   - Verify the directory context
   - Understand what the command does

2. **Use `--force` Sparingly**
   - Only when absolutely necessary
   - Double-check dangerous commands
   - Consider editing commands first (`e` option)

3. **Keep API Key Secure**
   - Never commit to git
   - Never share publicly
   - Use Keychain (automatic)

4. **Review Logs Periodically**
   ```bash
   tail -f ~/.grok_terminal/grok.log
   ```

5. **Use `--no-log` for Sensitive Queries**
   ```bash
   NextEleven AI: list processes --no-log
   ```

6. **Verify Command Context**
   - Check "Would run in" directory
   - Ensure you're in the right location
   - Use absolute paths when needed

7. **Update Regularly**
   - Pull latest changes
   - Run `install.sh` to update
   - Check for security patches

---

## Examples & Use Cases

### Development Workflows

**Git Operations:**
```bash
NextEleven AI: show me git commands to clean up old branches
NextEleven AI: explain git rebase vs merge
NextEleven AI: create a script to backup my git repos
```

**Code Navigation:**
```bash
NextEleven AI: find all functions that use the database connection
NextEleven AI: show me all TODO comments in the codebase
NextEleven AI: list all Python files modified in the last week
```

**Debugging:**
```bash
NextEleven AI: explain why this command failed: npm install
NextEleven AI: help me debug this error: permission denied
NextEleven AI: what does this error mean: ModuleNotFoundError
```

### System Administration

**File Management:**
```bash
NextEleven AI: find files larger than 100MB
NextEleven AI: list all log files older than 30 days
NextEleven AI: create a script to clean up temp files
```

**Process Management:**
```bash
NextEleven AI: show me all running Python processes
NextEleven AI: find processes using the most memory
NextEleven AI: kill all processes matching a pattern
```

**System Info:**
```bash
NextEleven AI: check disk usage and find what's taking space
NextEleven AI: show system resource usage
NextEleven AI: list all installed Homebrew packages
```

### Learning & Documentation

**Command Explanation:**
```bash
NextEleven AI: explain what this does: find . -name "*.log" -mtime +30 -delete
NextEleven AI: what's the difference between grep and find?
NextEleven AI: explain shell redirection operators
```

**Script Generation:**
```bash
NextEleven AI: create a backup script for my home directory
NextEleven AI: write a script to monitor disk space
NextEleven AI: generate a script to clean up old files
```

---

## Tips & Tricks

### 1. Use Interactive Mode for Complex Tasks

For multi-step operations, use interactive mode:
```bash
grok
# Then have a conversation
You: I need to refactor this code
eleven: [Provides step-by-step guidance]
You: Can you help me with the first step?
eleven: [Detailed instructions]
```

### 2. Combine with Other Tools

**eleven** works great with:
- `fzf` - For command selection
- `vim` - For command editing
- `git` - For version control
- `tmux` - For session management

### 3. Use Context Effectively

**eleven** knows your current directory and git status. Use this:
```bash
# In a git repo
NextEleven AI: what's the status and suggest next steps

# In a project directory
NextEleven AI: explain the structure of this project
```

### 4. Leverage History

Previous conversations are remembered:
```bash
# First query
NextEleven AI: I'm working on a Python project

# Later (in same session)
NextEleven AI: help me debug the error we saw earlier
```

### 5. Use Slash Commands

In interactive mode:
- `/help` - Quick reference
- `/clear` - Start fresh
- `/init` - Generate project file

---

## File Locations

### Installation Files
- `~/.grok_terminal/grok_agent.py` - Main Python script
- `~/.grok_terminal/grok.zsh` - Zsh plugin
- `~/.grok_terminal/security_utils.py` - Security utilities
- `~/.grok_terminal/hooks/` - Custom hooks directory

### Data Files
- `~/.grok_terminal_history.json` - Conversation history
- `~/.grok_terminal/todos.json` - Saved todos
- `~/.grok_terminal_config.json` - User configuration
- `~/.grok_terminal/grok.log` - Application logs

### Configuration
- `~/.zshrc` - Contains source line for grok.zsh

---

## Command Reference

### Interactive Mode

```bash
grok                                    # Start interactive mode
grok --interactive                      # Same as above
grok --force                            # Allow dangerous commands
grok --no-log                           # Disable logging
grok --dangerously-skip-permissions     # Skip permission prompts
```

### Prefix Mode

```bash
NextEleven AI: <query>                  # Basic query
NextEleven AI: <query> --no-log         # Without logging
NextEleven AI: <query> --force          # Allow dangerous commands
```

### Slash Commands (Interactive Mode)

```
/help                                   # Show help
/init                                   # Generate ELEVEN.md
/clear                                  # Clear history
/hooks                                  # Show hooks directory
exit                                    # Exit interactive mode
```

---

## Support

### Getting Help

1. **Check Logs:**
   ```bash
   tail -f ~/.grok_terminal/grok.log
   ```

2. **Verify Installation:**
   ```bash
   grok --help
   type NextEleven
   ```

3. **Test API Connection:**
   ```bash
   python3 ~/.grok_terminal/grok_agent.py --help
   ```

4. **Check Configuration:**
   ```bash
   cat ~/.grok_terminal_config.json
   ```

### Common Error Messages

| Error | Solution |
|-------|----------|
| "API key not found" | Run `install.sh` or add key manually |
| "Rate limit exceeded" | Wait or upgrade API plan |
| "Invalid API key" | Check your NextEleven API key |
| "Command not found" | Verify installation and `source ~/.zshrc` |
| "Permission denied" | Check file permissions and Keychain access |

---

## FAQ

### Q: Can I use this with other shells?

**A:** Currently designed for zsh on macOS. Bash support may be added in future versions.

### Q: Is my API key secure?

**A:** Yes! API keys are stored encrypted in macOS Keychain, never in plain text files.

### Q: Can I customize the AI's behavior?

**A:** Yes! Modify the system prompt in `grok_agent.py` or create custom hooks.

### Q: Does this work offline?

**A:** Limited offline support via local command suggestions. Full features require API access.

### Q: How much does this cost?

**A:** The tool is free. You only pay for NextEleven API usage (check their pricing).

### Q: Can I use my own API endpoint?

**A:** Currently uses NextEleven API. Custom endpoints may be supported in future versions.

### Q: How do I update?

**A:** Pull latest changes and run `install.sh` again.

### Q: Can I disable command execution?

**A:** Commands always require your confirmation. There's no auto-execution.

---

## Changelog

### Version 1.0 (January 2026)
- ✅ Initial release
- ✅ Interactive and prefix modes
- ✅ Tool calling system
- ✅ History persistence
- ✅ Security features
- ✅ White-label branding

---

## License

See [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the macOS terminal community**

**Powered by NextEleven's eleven AI**
