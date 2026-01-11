# Grok-Code Integration Guide
## Using Your Specialized Agents from grokcode.vercel.app

This guide shows you how to integrate your 20 specialized agents from [Grok-Code](https://grokcode.vercel.app/) into the terminal agent.

---

## Overview

Your Grok-Code system has:
- **Live Site**: https://grokcode.vercel.app/
- **Repository**: https://github.com/seanebones-lang/Grok-Code
- **20 Specialized Agents** with tools trained for specific tasks

---

## Integration Options

### Option 1: Custom API Endpoint (If Grok-Code Has API)

If your Grok-Code system exposes an API endpoint, configure it:

```json
{
  "model": "your-agent-name",
  "api_endpoint": "https://grokcode.vercel.app/api/chat",
  "temperature": 0.1,
  "max_tokens": 2048
}
```

Or use via command line:
```bash
eleven --endpoint "https://grokcode.vercel.app/api/chat" --model "coding-agent"
```

### Option 2: Agent Endpoint Mapping

Map specific agents to their endpoints:

```json
{
  "model": "grok-4.1-fast",
  "api_endpoint": "https://api.x.ai/v1/chat/completions",
  "agent_endpoints": {
    "coding-agent": "https://grokcode.vercel.app/api/agents/coding",
    "docs-agent": "https://grokcode.vercel.app/api/agents/docs",
    "devops-agent": "https://grokcode.vercel.app/api/agents/devops",
    "testing-agent": "https://grokcode.vercel.app/api/agents/testing"
  },
  "temperature": 0.1,
  "max_tokens": 2048
}
```

Then use:
```bash
eleven --model "coding-agent"  # Automatically uses mapped endpoint
```

### Option 3: Same xAI API, Different Model Names

If your specialized agents are accessible via xAI API with different model names:

```json
{
  "model": "grok-coding-agent",
  "api_endpoint": "https://api.x.ai/v1/chat/completions",
  "temperature": 0.1,
  "max_tokens": 4096
}
```

---

## Setup Steps

### Step 1: Create Configuration

Create `~/.grok_terminal_config.json`:

```json
{
  "model": "grok-4.1-fast",
  "api_endpoint": "https://api.x.ai/v1/chat/completions",
  "agent_endpoints": {
    "coding": "your-coding-agent-endpoint",
    "docs": "your-docs-agent-endpoint",
    "testing": "your-testing-agent-endpoint"
  },
  "temperature": 0.1,
  "max_tokens": 2048
}
```

### Step 2: Test Connection

Test if your endpoint works:
```bash
curl -X POST "https://your-endpoint/api/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "your-agent", "messages": [{"role": "user", "content": "test"}]}'
```

### Step 3: Use the Agents

```bash
# Use default model
eleven

# Use specific agent
eleven --model "coding-agent"

# Use custom endpoint
eleven --endpoint "https://grokcode.vercel.app/api/chat" --model "your-agent"
```

---

## Creating Agent Shortcuts

Create shortcuts for your specialized agents:

### Example: Add to grok.zsh

```zsh
# Coding agent shortcut
eleven-coding() {
    eleven --model "coding-agent" "$@"
}

# Docs agent shortcut
eleven-docs() {
    eleven --model "docs-agent" "$@"
}

# Testing agent shortcut
eleven-testing() {
    eleven --model "testing-agent" "$@"
}
```

Then use:
```bash
eleven-coding "explain this code"
eleven-docs "generate documentation"
eleven-testing "write unit tests"
```

---

## Tool Integration

If your specialized agents use different tool formats, we can adapt:

### Current Tool Format:
```xml
<tool name="ToolName">
  <param name="param1">value1</param>
</tool>
```

### If Your Agents Use Different Format:

Share the format and I'll add adapters to convert between formats.

---

## Next Steps

To complete the integration, please provide:

1. **API Endpoint Details**:
   - Does grokcode.vercel.app expose an API?
   - What's the endpoint URL?
   - Authentication method?

2. **Agent Names**:
   - List of your 20 agent names/IDs
   - Example: `["coding-agent", "docs-agent", "testing-agent", ...]`

3. **Request Format**:
   - Same as chat completions?
   - Custom format?
   - Example request/response

4. **Tool Format**:
   - Same XML format?
   - Different format?
   - Example tool call

---

## Example Configuration

Once you provide the details, here's what the config might look like:

```json
{
  "model": "grok-4.1-fast",
  "api_endpoint": "https://api.x.ai/v1/chat/completions",
  "agent_endpoints": {
    "coding": "https://grokcode.vercel.app/api/agents/coding",
    "docs": "https://grokcode.vercel.app/api/agents/docs",
    "testing": "https://grokcode.vercel.app/api/agents/testing",
    "security": "https://grokcode.vercel.app/api/agents/security",
    "devops": "https://grokcode.vercel.app/api/agents/devops"
  },
  "temperature": 0.1,
  "max_tokens": 4096,
  "cache_enabled": true
}
```

---

## Quick Start

Right now, you can already use model overrides:

```bash
# If agents are accessible via xAI API with custom model names
eleven --model "your-specialized-agent-name"

# If you have a custom endpoint
eleven --endpoint "https://your-endpoint/api" --model "your-agent"
```

**Share your agent details and I'll create the complete integration!**
