# Launch Instructions - Copy & Paste Ready

## 🚀 Quick Start (One Command at a Time)

### STEP 1: Open Terminal and Navigate to Project

Copy and paste this command:

```bash
cd "/Users/nexteleven/Desktop/Eleven in your Terminal/Eleven-Term"
```

---

### STEP 2: Verify System is Ready

Copy and paste this command:

```bash
python3 grok_agent.py --help
```

**Expected Output:** You should see usage information with all available options.

---

### STEP 3: Launch System with Full Access (Recommended)

Copy and paste this command:

```bash
python3 grok_agent.py --interactive --force --dangerously-skip-permissions
```

**OR** use the convenience script:

```bash
./launch_full_access.sh
```

**What happens:** The system will start in interactive mode with full permissions.

---

### STEP 4: First-Time Creator Verification (One-Time Setup)

If you want to verify as the creator for full override access, copy and paste:

```bash
python3 grok_agent.py --verify-creator
```

**What happens:** 
- You'll be prompted to enter your verification code
- Enter: `071225`
- Your identity will be stored securely in macOS Keychain
- This only needs to be done once

---

### STEP 5: Using the System

Once launched, you can:

1. **Ask questions normally:**
   ```
   What files are in this directory?
   ```

2. **Request commands:**
   ```
   Show me the git status
   ```

3. **Request file operations:**
   ```
   Read the README.md file
   ```

4. **Request system operations:**
   ```
   List all Python files
   ```

5. **Type `/help` for commands:**
   - `/help` - Show available commands
   - `/init` - Initialize new conversation
   - `/clear` - Clear conversation history
   - `/hooks` - Show available hooks

6. **Exit:** Press `Ctrl+C` or type `exit`

---

## 🎯 Alternative Launch Methods

### Launch with Safety Prompts (Default Security)

Copy and paste:

```bash
python3 grok_agent.py --interactive
```

**What this does:** Prompts before executing dangerous commands.

---

### Launch for Single Query (Non-Interactive)

Copy and paste:

```bash
python3 grok_agent.py "your question here"
```

**Example:**

```bash
python3 grok_agent.py "What files are in the current directory?"
```

---

### Launch with Specific Agent

Copy and paste:

```bash
python3 grok_agent.py --interactive --model security --force --dangerously-skip-permissions
```

**Available agents:** security, performance, testing, etc.

To see all agents:

```bash
python3 grok_agent.py --list-agents
```

---

## 📋 Quick Reference

### Full Access Mode (Recommended)
```bash
python3 grok_agent.py --interactive --force --dangerously-skip-permissions
```

### With Convenience Script
```bash
./launch_full_access.sh
```

### Safe Mode (with prompts)
```bash
python3 grok_agent.py --interactive
```

### Single Query
```bash
python3 grok_agent.py "your question"
```

---

## ⚠️ Important Notes

1. **First Launch:** May prompt for sudo password (stored securely in Keychain)
2. **Creator Verification:** Only needed once (code: 071225)
3. **Full Access:** Use `--force --dangerously-skip-permissions` for automatic execution
4. **Sudo:** System automatically uses sudo when needed (for accessibility)

---

## 🔧 Troubleshooting

If you get "API key not found":
```bash
./install.sh
```

If you get "Permission denied" on launch script:
```bash
chmod +x launch_full_access.sh
```

If Python not found:
```bash
python3 --version
```
(Should show Python 3.12+)
