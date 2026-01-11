#!/bin/bash
TEMP_DIR=$(mktemp -d)
git clone --depth 1 "https://github.com/seanebones-lang/Grok-Code.git" "$TEMP_DIR" 2>/dev/null

echo "📋 COMPLETE LIST OF 20 SPECIALIZED AGENTS:"
echo ""

# Extract agent IDs from the SPECIALIZED_AGENTS object
grep -E "^\s+[a-zA-Z]+: \{" "$TEMP_DIR/src/lib/specialized-agents.ts" | \
  sed 's/.*\([a-zA-Z]*\):.*/\1/' | \
  sort | \
  nl -w2 -s'. ' | \
  sed 's/^/  /'

echo ""
echo "🔗 Available agent endpoints:"
find "$TEMP_DIR/src/app/api/agent" -name "route.ts" 2>/dev/null | \
  sed 's|.*/agent/||' | \
  sed 's|/route.ts||' | \
  sort | \
  nl -w2 -s'. /api/agent/' | \
  sed 's/^/  /'

echo ""
echo "📡 Main API endpoint: /api/chat"
echo "📡 Agents list endpoint: /api/agents"

rm -rf "$TEMP_DIR"
