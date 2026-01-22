#!/bin/sh
set -e

# Replace placeholder with actual API key at runtime
if [ -n "$GEMINI_API_KEY" ]; then
    find /usr/share/nginx/html -name "*.js" -exec sed -i "s|__GEMINI_API_KEY_PLACEHOLDER__|$GEMINI_API_KEY|g" {} \;
fi

exec "$@"
