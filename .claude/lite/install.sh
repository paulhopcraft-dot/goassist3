#!/bin/bash
# Install Claude Code Toolkit Lite globally
# Run: ./install.sh

TARGET_DIR="$HOME/.claude/commands"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Claude Code Toolkit Lite..."

# Create directory if needed
mkdir -p "$TARGET_DIR"

# Copy command files
for cmd in status.md continue.md autonomous.md review.md handoff.md; do
    if [ -f "$SCRIPT_DIR/$cmd" ]; then
        cp "$SCRIPT_DIR/$cmd" "$TARGET_DIR/"
        echo "Installed: $cmd"
    fi
done

echo ""
echo "Done! Commands available globally:"
echo "  /status     - Check project state"
echo "  /continue   - Resume work"
echo "  /autonomous - Work without interruption"
echo "  /review     - Quick code review"
echo "  /handoff    - End session cleanly"
echo ""
echo "Run 'claude' from any directory to use."
