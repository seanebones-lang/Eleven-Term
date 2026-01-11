#!/bin/bash
# Discover Grok-Code API Endpoints

BASE_URL="https://grokcode.vercel.app"
echo "🔍 Discovering API endpoints for ${BASE_URL}..."
echo ""

# Common Next.js API patterns
endpoints=(
    "/api/chat"
    "/api/completions"
    "/api/agents"
    "/api/agent"
    "/api/v1/chat"
    "/api/v1/completions"
    "/api/v1/agents"
    "/api/chat/completions"
)

found_endpoints=()

for endpoint in "${endpoints[@]}"; do
    full_url="${BASE_URL}${endpoint}"
    status=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "${full_url}" 2>/dev/null)
    
    if [ "$status" != "404" ] && [ "$status" != "000" ]; then
        echo "✅ Found: ${full_url} (HTTP $status)"
        found_endpoints+=("${endpoint}")
        
        # Try to get more info
        if [ "$status" = "200" ] || [ "$status" = "405" ]; then
            echo "   Method allowed"
        fi
    fi
done

if [ ${#found_endpoints[@]} -eq 0 ]; then
    echo "⚠️  No standard API endpoints found"
    echo ""
    echo "📋 Please check:"
    echo "   1. Your Grok-Code repo for API routes"
    echo "   2. Vercel dashboard for serverless functions"
    echo "   3. Or share how agents are accessed"
else
    echo ""
    echo "✅ Found ${#found_endpoints[@]} potential endpoint(s)"
    echo ""
    echo "Test with:"
    echo "  eleven --endpoint \"${BASE_URL}${found_endpoints[0]}\" --model \"agent-name\""
fi

echo ""
