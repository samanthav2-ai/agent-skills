#!/bin/bash
# Start ClawdCursor with virtual display and Ollama backend

set -e

CLAWD_CURSOR_DIR="${CLAWD_CURSOR_DIR:-$HOME/clawd/clawd-cursor}"
PORT="${PORT:-3847}"
LOG_FILE="${LOG_FILE:-/tmp/clawd-cursor.log}"

cd "$CLAWD_CURSOR_DIR"

echo "🐾 ClawdCursor Startup"
echo "   Dir: $CLAWD_CURSOR_DIR"
echo "   Port: $PORT"

# Kill any existing instance
pkill -f "node dist/index.js start" 2>/dev/null || true
sleep 1

# Start Ollama if not running
export OLLAMA_MODELS=/data/ollama/models
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "   Starting Ollama..."
    nohup /data/ollama/bin/ollama serve > /data/ollama/serve.log 2>&1 &
    sleep 3
fi

if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "   ✅ Ollama ready"
else
    echo "   ⚠️  Ollama not available (LLM features disabled)"
fi

# Start ClawdCursor with Xvfb
echo "   Starting with virtual display..."
nohup xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
    node dist/index.js start --port "$PORT" > "$LOG_FILE" 2>&1 &

CLAWD_PID=$!
sleep 5

# Verify it started
if curl -s "http://127.0.0.1:$PORT/status" > /dev/null 2>&1; then
    echo "   ✅ ClawdCursor running at http://127.0.0.1:$PORT"
    echo "   PID: $CLAWD_PID"
    echo "   Log: $LOG_FILE"
else
    echo "   ⚠️  ClawdCursor may still be starting..."
    echo "   PID: $CLAWD_PID"
    echo "   Check: tail -f $LOG_FILE"
fi
