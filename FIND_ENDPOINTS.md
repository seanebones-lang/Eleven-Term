# Finding Your Grok-Code API Endpoints
## Guide to Discovering API Endpoints from grokcode.vercel.app

Your Grok-Code system is deployed at [https://grokcode.vercel.app/](https://grokcode.vercel.app/) and has 20 specialized agents. Here's how to find the API endpoints.

---

## Quick Discovery Steps

### Step 1: Check Your Repository Structure

In your [Grok-Code repository](https://github.com/seanebones-lang/Grok-Code), look for API routes:

#### Next.js App Router (src/app/api/)
```bash
# Check for API routes
ls -la src/app/api/
# Look for files like:
# - src/app/api/chat/route.ts
# - src/app/api/completions/route.ts
# - src/app/api/agents/route.ts
# - src/app/api/agents/[id]/route.ts
```

#### Next.js Pages Router (pages/api/)
```bash
# Check for API routes
ls -la pages/api/
# Look for files like:
# - pages/api/chat.ts
# - pages/api/completions.ts
# - pages/api/agents.ts
# - pages/api/agents/[id].ts
```

#### Custom API Folder (src/api/)
```bash
# Check for API files
ls -la src/api/
```

### Step 2: Check Vercel Configuration

In your Vercel dashboard:
1. Go to your project: grokcode
2. Check **Settings** → **Environment Variables**
3. Look for API endpoint variables
4. Check **Deployments** → **Functions** to see serverless function routes

### Step 3: Test Common Endpoints

Test these common patterns:

```bash
# Test chat endpoint
curl -X POST "https://grokcode.vercel.app/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'

# Test completions endpoint
curl -X POST "https://grokcode.vercel.app/api/completions" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'

# Test agents endpoint
curl "https://grokcode.vercel.app/api/agents"

# Test specific agent
curl "https://grokcode.vercel.app/api/agents/coding"
```

### Step 4: Check Environment Variables

In your repo, check for:
- `.env` files
- `.env.local` files
- `vercel.json` configuration
- `next.config.ts` configuration

Look for:
- API endpoint URLs
- Agent configuration
- Model mappings

---

## Common Next.js API Patterns

### Pattern 1: Single Chat Endpoint
```
POST /api/chat
Body: {
  "messages": [...],
  "model": "agent-name" (optional)
}
```

### Pattern 2: Agent-Specific Endpoints
```
POST /api/agents/:agentId
POST /api/agents/coding
POST /api/agents/docs
```

### Pattern 3: Completions Endpoint
```
POST /api/completions
Body: {
  "messages": [...],
  "model": "agent-name"
}
```

---

## If Agents Use xAI API Directly

If your specialized agents are accessed via xAI API with custom model names:

### Option 1: Use Model Name Override
```bash
eleven --model "your-specialized-agent-name"
```

### Option 2: Configure in Config File
```json
{
  "model": "your-agent-name",
  "api_endpoint": "https://api.x.ai/v1/chat/completions"
}
```

---

## If Agents Use Custom Endpoint

If your Grok-Code system has a custom API endpoint:

### Option 1: Use Endpoint Override
```bash
eleven --endpoint "https://grokcode.vercel.app/api/chat" --model "agent-name"
```

### Option 2: Configure in Config File
```json
{
  "model": "agent-name",
  "api_endpoint": "https://grokcode.vercel.app/api/chat"
}
```

### Option 3: Agent Endpoint Mapping
```json
{
  "model": "default",
  "api_endpoint": "https://api.x.ai/v1/chat/completions",
  "agent_endpoints": {
    "coding-agent": "https://grokcode.vercel.app/api/agents/coding",
    "docs-agent": "https://grokcode.vercel.app/api/agents/docs",
    "testing-agent": "https://grokcode.vercel.app/api/agents/testing"
  }
}
```

Then use:
```bash
eleven --model "coding-agent"  # Uses mapped endpoint
```

---

## Discovery Script

Create a script to test endpoints:

```bash
#!/bin/bash
# discover-endpoints.sh

BASE_URL="https://grokcode.vercel.app"

echo "🔍 Discovering API endpoints..."
echo ""

# Test common routes
endpoints=(
    "/api/chat"
    "/api/completions"
    "/api/agents"
    "/api/agent"
    "/api/v1/chat"
    "/api/v1/completions"
    "/api/v1/agents"
)

for endpoint in "${endpoints[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}${endpoint}" 2>/dev/null)
    if [ "$status" != "404" ] && [ "$status" != "000" ]; then
        echo "✅ ${BASE_URL}${endpoint} (HTTP $status)"
        
        # Try GET request
        if [ "$status" = "200" ] || [ "$status" = "405" ]; then
            echo "   Response: $(curl -s "${BASE_URL}${endpoint}" | head -c 200)"
        fi
    fi
done

echo ""
echo "📋 Next steps:"
echo "   1. Check your repo for API routes"
echo "   2. Check Vercel dashboard for function routes"
echo "   3. Share the endpoint structure with me"
echo ""
```

---

## What I Need From You

To complete the integration, please provide:

1. **API Endpoint Structure**:
   - Does grokcode.vercel.app expose an API?
   - What's the base endpoint? (e.g., `/api/chat`, `/api/agents`)
   - How are agents accessed? (query param, path param, model name)

2. **20 Agent Names/IDs**:
   - List all 20 agent names
   - Example: `["coding-agent", "docs-agent", "testing-agent", ...]`

3. **Request Format**:
   - Same as chat completions? `{"messages": [...], "model": "..."}`
   - Or custom format?

4. **Authentication**:
   - Same xAI API key?
   - Bearer token?
   - Custom header?

5. **Tool Format**:
   - Same XML format? `<tool name="..."><param>...</tool>`
   - Or different format?

Once you provide these, I can:
✅ Create complete integration
✅ Add agent shortcuts (`eleven-coding`, etc.)
✅ Set up endpoint mapping
✅ Configure all 20 agents

---

## Quick Test Command

To test if your site has an API, try:

```bash
# Test if API exists
curl -X OPTIONS "https://grokcode.vercel.app/api" -v

# Test chat endpoint (if exists)
curl -X POST "https://grokcode.vercel.app/api/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
```

---

**Share your endpoint structure and I'll integrate it!**
