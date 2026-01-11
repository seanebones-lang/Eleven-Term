#!/bin/bash
# Live API integration test

API_KEY=$(security find-generic-password -s grok-terminal -a xai-api-key -w 2>/dev/null)

if [ -z "$API_KEY" ]; then
    echo "⚠️  API key not found - cannot run live API tests"
    exit 0
fi

echo "🔍 LIVE API INTEGRATION TESTS"
echo "=============================="
echo ""

# Test 1: Test basic endpoint
echo "[Test 1] Testing basic /api/chat endpoint..."
response=$(curl -s -X POST "https://grokcode.vercel.app/api/chat" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"message": "hello", "model": "grok-4.1-fast"}' 2>&1)

if echo "$response" | grep -q "content\|Hello"; then
    echo "  ✅ PASS - Endpoint responds"
else
    echo "  ❌ FAIL - Endpoint error"
    echo "  Response: $response" | head -3
fi

# Test 2: Test with security agent
echo ""
echo "[Test 2] Testing Security Agent..."
response=$(curl -s -X POST "https://grokcode.vercel.app/api/chat" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"message": "test security", "model": "grok-4.1-fast", "mode": "agent", "agent": "security"}' 2>&1)

if echo "$response" | grep -q "content\|data:"; then
    echo "  ✅ PASS - Security agent responds"
else
    echo "  ❌ FAIL - Security agent error"
    echo "  Response: $response" | head -3
fi

# Test 3: Test with performance agent
echo ""
echo "[Test 3] Testing Performance Agent..."
response=$(curl -s -X POST "https://grokcode.vercel.app/api/chat" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"message": "test performance", "model": "grok-4.1-fast", "mode": "agent", "agent": "performance"}' 2>&1)

if echo "$response" | grep -q "content\|data:"; then
    echo "  ✅ PASS - Performance agent responds"
else
    echo "  ❌ FAIL - Performance agent error"
    echo "  Response: $response" | head -3
fi

echo ""
echo "✅ Live API tests complete"
