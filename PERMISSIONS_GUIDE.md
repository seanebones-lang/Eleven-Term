# System Permissions and Access Guide

## ♿ Accessibility Features

**AUTOMATIC SUDO DETECTION**: The system automatically detects when sudo is needed and uses it seamlessly. Your sudo password is stored securely in macOS Keychain (one-time setup). This makes the system fully accessible - you don't need to manually enter sudo commands or passwords.

## 🔐 Current Permission Level

The NextEleven Terminal Agent runs with **YOUR user's permissions**. This means:

✅ **Full Access Capabilities:**
- Execute any command your user can execute
- Read/write any file/directory your user can access
- Access network resources (for API calls)
- Use macOS Keychain (for secure API key storage)
- File system operations (create, delete, modify files)
- Process management (run, kill processes your user can manage)
- Install packages (if you have sudo/admin access when prompted)

⚠️ **Limitations (Same as Your User):**
- Cannot access files/directories requiring root permissions (unless you use `sudo`)
- Cannot modify system files (unless you have admin access and use `sudo`)
- Subject to macOS security restrictions (Full Disk Access, etc.)
- Cannot execute commands requiring different user permissions

## 🚀 Automatic Sudo (Accessibility Feature)

The system **automatically detects** when sudo is needed and uses it seamlessly:

1. **First time**: You'll be prompted once to enter your sudo password
2. **Stored securely**: Password is stored in macOS Keychain (encrypted)
3. **Automatic**: System automatically uses sudo when permission errors occur
4. **No prompts**: After first setup, no more password prompts needed

**How it works:**
- System tries command without sudo first
- If permission error detected → automatically retries with sudo
- Uses stored password from Keychain
- Works seamlessly in the background

## 🚀 Enabling Full Permissions (Your User Level)

To give the system full access to do anything you can do, use these flags:

### For Single Commands:
```bash
python3 grok_agent.py --force --dangerously-skip-permissions "your command here"
```

### For Interactive Mode:
```bash
python3 grok_agent.py --interactive --force --dangerously-skip-permissions
```

### Flags Explained:

- **`--force`**: Allows dangerous commands (rm, sudo, etc.) to execute without extra warnings
- **`--dangerously-skip-permissions`**: Skips confirmation prompts - commands execute immediately

## 🔒 Security Features (Bypassed with Flags Above)

By default, the system has these safety features:

1. **Dangerous Command Detection**: Flags risky operations (rm, sudo, etc.)
2. **Confirmation Prompts**: Asks for `y/n` confirmation before executing dangerous commands
3. **Command Validation**: Validates command structure before execution
4. **Input Sanitization**: Cleans input to prevent injection attacks

**When you use `--force` and `--dangerously-skip-permissions`, these protections are bypassed.**

## 🛡️ macOS Security Permissions

The system respects macOS security settings:

### Full Disk Access
If you need to access certain directories, you may need to grant Full Disk Access:
1. System Settings → Privacy & Security → Full Disk Access
2. Add Terminal.app (or your terminal app)
3. Restart terminal

### Network Access
- API calls require network access (automatically granted)
- HTTPS connections are allowed by default

### Keychain Access
- API keys are stored in macOS Keychain
- First use will prompt for Keychain access (click "Allow")

## 📝 Example: Full Access Setup

To set up the system for full access (your permission level):

```bash
# Interactive mode with full permissions
python3 grok_agent.py --interactive --force --dangerously-skip-permissions

# Or create an alias for convenience
alias grok-full="python3 grok_agent.py --interactive --force --dangerously-skip-permissions"
```

Then in interactive mode, the system can:
- Execute any command without prompts
- Access any file you can access
- Perform system operations (install packages, modify files, etc.)
- Run administrative commands (if you provide sudo password when prompted)

## ⚠️ Important Notes

1. **The system runs as YOUR user** - it cannot exceed your permissions
2. **If you need root/admin access** - you'll need to use `sudo` commands (system will prompt for password)
3. **macOS restrictions apply** - certain system directories may require Full Disk Access
4. **Security is YOUR responsibility** - with `--force` and `--dangerously-skip-permissions`, commands execute immediately

## 🔧 Troubleshooting Permissions

If the system cannot access something you can access:

1. **Check file permissions:**
   ```bash
   ls -la /path/to/file
   ```

2. **Grant Full Disk Access** (System Settings → Privacy & Security)

3. **Use sudo if needed** (system will prompt for password)

4. **Check Terminal app permissions** in System Settings

## ✅ Current Status

The system is configured to:
- ✅ Run with your user permissions
- ✅ Execute commands via subprocess (same as manual execution)
- ✅ Access files/directories your user can access
- ✅ Use security features by default (can be bypassed with flags)
- ✅ Respect macOS security restrictions (same as you would)

**To enable full access at your permission level, simply use:**
```bash
python3 grok_agent.py --interactive --force --dangerously-skip-permissions
```
