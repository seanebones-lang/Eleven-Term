#!/bin/bash
# Fetch Grok-Code repository information

REPO_URL="https://github.com/seanebones-lang/Grok-Code.git"
TEMP_DIR=$(mktemp -d)
echo "📥 Cloning Grok-Code repository..."

# Clone repository (shallow clone for speed)
git clone --depth 1 "$REPO_URL" "$TEMP_DIR" 2>&1 | head -20

if [ -d "$TEMP_DIR" ] && [ -n "$(ls -A "$TEMP_DIR" 2>/dev/null)" ]; then
    echo ""
    echo "✅ Repository cloned successfully"
    echo ""
    echo "📁 Repository structure:"
    find "$TEMP_DIR" -maxdepth 3 -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | head -30 | sed "s|$TEMP_DIR/||"
    
    echo ""
    echo "🔍 Looking for API routes..."
    find "$TEMP_DIR" -path "*/api/*" -type f \( -name "route.ts" -o -name "route.js" -o -name "*.ts" -o -name "*.js" \) 2>/dev/null | sed "s|$TEMP_DIR/||"
    
    echo ""
    echo "🔍 Looking for agent configuration..."
    find "$TEMP_DIR" -type f \( -name "*agent*" -o -name "*config*" -o -name "*model*" \) 2>/dev/null | head -20 | sed "s|$TEMP_DIR/||"
    
    echo ""
    echo "📋 Examining key files..."
    
    # Check for API route
    if [ -f "$TEMP_DIR/src/app/api/chat/route.ts" ]; then
        echo "Found: src/app/api/chat/route.ts"
        head -100 "$TEMP_DIR/src/app/api/chat/route.ts"
    elif [ -f "$TEMP_DIR/pages/api/chat.ts" ]; then
        echo "Found: pages/api/chat.ts"
        head -100 "$TEMP_DIR/pages/api/chat.ts"
    fi
    
    echo ""
    echo "🧹 Cleaning up..."
    rm -rf "$TEMP_DIR"
else
    echo "❌ Failed to clone repository"
fi

