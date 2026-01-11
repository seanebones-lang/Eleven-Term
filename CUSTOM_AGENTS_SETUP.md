# Custom Specialized Agents Setup Guide
## Using Your Specialized Grok Agents with Tools

This guide shows you how to configure and use your specialized agents that are trained for specific tasks.

---

## Quick Setup

### Option 1: Single Custom Model (Simplest)

Create or edit `~/.grok_terminal_config.json`:

```json
{
  "model": "your-specialized-agent-name",
  "temperature": 0.1,
  "max_tokens": 2048
}
```

**Example:**
```json
{
  "model": "grok-coding-agent",
  "temperature": 0.1,
  "max_tokens": 4096
}
```

### Option 2: Multiple Specialized Agents

You can create multiple config files and switch between them:

```bash
# Create configs for different agents
cat > ~/.grok_terminal_config_coding.json << 'EOF'
{
  "model": "grok-coding-agent",
  "temperature": 0.1,
  "max_tokens": 4096
}
EOF

cat > ~/.grok_terminal_config_docs.json << 'EOF'
{
  "model": "grok-docs-agent",
  "temperature": 0.2,
  "max_tokens": 2048
}
EOF
```

Then use them:
```bash
# Use coding agent
cp ~/.grok_terminal_config_coding.json ~/.grok_terminal_config.json
eleven

# Switch to docs agent
cp ~/.grok_terminal_config_docs.json ~/.grok_terminal_config.json
eleven
```

---

## Custom API Endpoints

If your specialized agents use a different API endpoint, you can modify the code:

1. Edit `grok_agent.py`
2. Find: `API_ENDPOINT = "https://api.x.ai/v1/chat/completions"`
3. Change to your endpoint, or add endpoint to config

**Or** add endpoint support to config:

```json
{
  "model": "your-agent",
  "api_endpoint": "https://your-custom-endpoint.com/v1/chat/completions",
  "temperature": 0.1
}
```

---

## Tool Integration

If your specialized agents have custom tools, they should work with the existing tool calling format:

```xml
<tool name="YourCustomTool">
  <param name="param1">value1</param>
  <param name="param2">value2</param>
</tool>
```

The system will extract and execute tools automatically.

---

## Model Switcher Script

Create a helper script to switch between agents:

```bash
#!/bin/bash
# ~/bin/switch-agent.sh

case "$1" in
  coding)
    cp ~/.grok_terminal_config_coding.json ~/.grok_terminal_config.json
    echo "Switched to coding agent"
    ;;
  docs)
    cp ~/.grok_terminal_config_docs.json ~/.grok_terminal_config.json
    echo "Switched to docs agent"
    ;;
  default)
    cp ~/.grok_terminal_config_default.json ~/.grok_terminal_config.json
    echo "Switched to default agent"
    ;;
  *)
    echo "Usage: switch-agent [coding|docs|default]"
    ;;
esac
```

---

## Questions to Answer

To fully integrate your specialized agents, please provide:

1. **Model Names**: Exact model names/IDs
   - Example: `grok-coding-agent`, `grok-devops-agent`, etc.

2. **API Endpoint**: 
   - Same xAI endpoint? (`https://api.x.ai/v1/chat/completions`)
   - Or custom endpoint?

3. **API Key**:
   - Same key for all agents?
   - Or different keys per agent?

4. **Tool Format**:
   - Same XML format? (`<tool name="...">`)
   - Or different format?

5. **Special Features**:
   - Any special parameters needed?
   - Custom headers?
   - Different authentication?

---

## Next Steps

Once you provide the details, I can:
- ✅ Add model switcher command
- ✅ Support multiple endpoints
- ✅ Integrate custom tools
- ✅ Add agent-specific configurations
- ✅ Create shortcuts for each agent

**Share your agent details and I'll customize the integration!**
