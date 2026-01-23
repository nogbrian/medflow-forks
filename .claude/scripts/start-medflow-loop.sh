#!/bin/bash
# MedFlow Ralph Loop - Setup Script
#
# Usage:
#   ./start-medflow-loop.sh [command-file] [--max-iterations N] [--promise TEXT]
#
# Examples:
#   ./start-medflow-loop.sh medflow-build
#   ./start-medflow-loop.sh medflow-sprint --max-iterations 20
#   ./start-medflow-loop.sh medflow-build --promise "BUILD_COMPLETE" --max-iterations 100

set -e

# Defaults
COMMAND_FILE="medflow-build"
MAX_ITERATIONS=50
COMPLETION_PROMISE="BUILD_COMPLETE"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --promise)
            COMPLETION_PROMISE="$2"
            shift 2
            ;;
        *)
            COMMAND_FILE="$1"
            shift
            ;;
    esac
done

# Resolve command file path
COMMAND_PATH=".claude/commands/${COMMAND_FILE}.md"
if [ ! -f "$COMMAND_PATH" ]; then
    echo "❌ Command file not found: $COMMAND_PATH"
    echo "Available commands:"
    ls .claude/commands/*.md 2>/dev/null | sed 's|.claude/commands/||;s|\.md||'
    exit 1
fi

# Read the command file content
PROMPT_BODY=$(cat "$COMMAND_PATH")

# Create the state file
STATE_FILE=".claude/ralph-loop.local.md"
cat > "$STATE_FILE" << EOF
---
iteration: 1
max_iterations: ${MAX_ITERATIONS}
completion_promise: ${COMPLETION_PROMISE}
started_at: $(date -Iseconds)
command: ${COMMAND_FILE}
---

${PROMPT_BODY}
EOF

echo "🚀 MedFlow Ralph Loop iniciado!"
echo "   Comando: ${COMMAND_FILE}"
echo "   Max iterações: ${MAX_ITERATIONS}"
echo "   Promise: ${COMPLETION_PROMISE}"
echo "   State file: ${STATE_FILE}"
echo ""
echo "Para cancelar: rm ${STATE_FILE}"
echo "Para verificar status: cat ${STATE_FILE} | head -10"
echo ""
echo "Agora inicie o Claude Code normalmente com:"
echo "   claude"
echo ""
echo "Ele entrará no loop automaticamente."
