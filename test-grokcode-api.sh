#!/bin/bash
# Test Grok-Code API endpoints

API_KEY=$(security find-generic-password -s grok-terminal -a xai-api-key -w 2>/dev/null)
BASE_URL="https://grokcode.vercel.app"

if [ -z "$API_KEY" ]; then
    echo "❌ API key not found in Keychain"
    exit 1
fi

echo "🔍 Testing Grok-Code API endpoints..."
echo ""

# Test 1: /api/chat with message field
echo "1️⃣  Testing /api/chat with 'message' field:"
response1=$(curl -s -X POST "${BASE_URL}/api/chat" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"message": "hello", "model": "grok-4.1-fast"}')
echo "$response1" | head -20
echo ""

# Test 2: /api/chat with messages array (xAI format)
echo "2️⃣  Testing /api/chat with 'messages' array (xAI format):"
response2=$(curl -s -X POST "${BASE_URL}/api/chat" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "hello"}], "model": "grok-4.1-fast"}')
echo "$response2" | head -20
echo ""

# Test 3: Check if there's an agents endpoint
echo "3️⃣  Testing /api/agents (GET):"
response3=$(curl -s "${BASE_URL}/api/agents" \
    -H "Authorization: Bearer ${API_KEY}")
echo "$response3" | head -20
echo ""

