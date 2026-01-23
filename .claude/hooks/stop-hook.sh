#!/bin/bash
# MedFlow Ralph Loop - Stop Hook
# Inspired by claude-code/plugins/ralph-wiggum
#
# This hook intercepts Claude Code's exit and re-injects the prompt
# if the completion promise hasn't been met.

STATE_FILE=".claude/ralph-loop.local.md"

# If no state file, allow exit normally
if [ ! -f "$STATE_FILE" ]; then
    exit 0
fi

# Read state from YAML frontmatter
ITERATION=$(sed -n 's/^iteration: //p' "$STATE_FILE" | head -1)
MAX_ITERATIONS=$(sed -n 's/^max_iterations: //p' "$STATE_FILE" | head -1)
COMPLETION_PROMISE=$(sed -n 's/^completion_promise: //p' "$STATE_FILE" | head -1)

# Default values
ITERATION=${ITERATION:-1}
MAX_ITERATIONS=${MAX_ITERATIONS:-50}
COMPLETION_PROMISE=${COMPLETION_PROMISE:-"BUILD_COMPLETE"}

# Check if max iterations reached
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
    echo "⚠️  Max iterations ($MAX_ITERATIONS) reached. Stopping loop." >&2
    rm -f "$STATE_FILE"
    exit 0
fi

# Check if completion promise was met in the last output
# The promise must be wrapped in <promise> tags (supports multiline)
LAST_OUTPUT=$(cat /tmp/claude-last-output 2>/dev/null || echo "")
if echo "$LAST_OUTPUT" | tr '\n' ' ' | grep -qE "<promise>[^<]*${COMPLETION_PROMISE}[^<]*</promise>"; then
    echo "✅ Completion promise met: $COMPLETION_PROMISE" >&2
    rm -f "$STATE_FILE"
    exit 0
fi

# Increment iteration
NEW_ITERATION=$((ITERATION + 1))
sed -i "s/^iteration: .*/iteration: $NEW_ITERATION/" "$STATE_FILE"

# Extract the prompt body (everything after the frontmatter)
PROMPT_BODY=$(sed -n '/^---$/,/^---$/!p' "$STATE_FILE" | tail -n +2)

# Add iteration context
ITERATION_CONTEXT="

---
## Iteração $NEW_ITERATION de $MAX_ITERATIONS

Você está na iteração $NEW_ITERATION. Revise o que já foi feito (git log, ls, etc.) e continue de onde parou.

Lembre-se:
- Não refaça trabalho já concluído
- Commite incrementalmente
- Se travar, mude de abordagem
- Quando TUDO estiver pronto, emita: <promise>${COMPLETION_PROMISE}</promise>
"

# Output the blocking decision (Claude Code hook protocol)
cat <<EOF
{
  "decision": "block",
  "reason": "${PROMPT_BODY}${ITERATION_CONTEXT}"
}
EOF
