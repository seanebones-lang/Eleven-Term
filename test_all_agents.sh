#!/bin/bash
# Test each of the 20 agents individually

API_KEY=$(security find-generic-password -s grok-terminal -a xai-api-key -w 2>/dev/null)

if [ -z "$API_KEY" ]; then
    echo "⚠️  API key not found - cannot run live agent tests"
    exit 0
fi

echo "🎯 TESTING ALL 20 AGENTS INDIVIDUALLY"
echo "======================================"
echo ""

AGENTS=(
    "security:agent"
    "performance:agent"
    "testing:agent"
    "documentation:agent"
    "migration:agent"
    "dependency:agent"
    "codeReview:review"
    "bugHunter:debug"
    "optimization:agent"
    "accessibility:agent"
    "orchestrator:orchestrate"
    "swarm:agent"
    "mobile:agent"
    "devops:agent"
    "database:agent"
    "api:agent"
    "uiux:agent"
    "aiml:agent"
    "data:agent"
    "fullstack:agent"
)

PASSED=0
FAILED=0

for agent_spec in "${AGENTS[@]}"; do
    agent_id="${agent_spec%%:*}"
    mode="${agent_spec##*:}"
    
    echo -n "[Test] $agent_id (mode: $mode)... "
    
    response=$(curl -s -X POST "https://grokcode.vercel.app/api/chat" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"test\", \"model\": \"grok-4.1-fast\", \"mode\": \"$mode\", \"agent\": \"$agent_id\"}" \
        -m 10 2>&1)
    
    if echo "$response" | grep -q "content\|data:"; then
        echo "✅ PASS"
        ((PASSED++))
    else
        echo "❌ FAIL"
        echo "    Response: $(echo "$response" | head -1 | cut -c1-60)..."
        ((FAILED++))
    fi
    
    sleep 0.5  # Rate limiting
done

echo ""
echo "======================================"
echo "TEST SUMMARY"
echo "======================================"
echo "Total Agents: ${#AGENTS[@]}"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL AGENTS WORKING!"
else
    echo "⚠️  Some agents failed (may be rate limiting or API issues)"
fi
