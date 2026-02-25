#!/usr/bin/env bash
#
# Monitor a coding agent running in a tmux session.
# Detects crashes and auto-resumes using agent's native resume command.
#
# Usage: ./scripts/monitor.sh <tmux-session> <agent>
#   agent: codex, claude, opencode, or pi
#
# Retry: 3min base, doubles on failure, resets when running. Stops after 5h.

set -uo pipefail

SESSION="${1:?Usage: monitor.sh <tmux-session> <agent>}"
AGENT="${2:?Usage: monitor.sh <tmux-session> <agent>}"

case "$AGENT" in
  codex|claude|opencode|pi) ;;
  *) echo "Unsupported agent: $AGENT" >&2; exit 1 ;;
esac

if ! printf '%s' "$SESSION" | grep -Eq '^[A-Za-z0-9._-]+$'; then
  echo "Invalid session name: $SESSION" >&2
  exit 1
fi

CODEX_SESSION_FILE="/tmp/${SESSION}.codex-session-id"
RETRY_COUNT=0
START_TS="$(date +%s)"
DEADLINE_TS=$(( START_TS + 18000 ))

while true; do
  NOW_TS="$(date +%s)"
  if [ "$NOW_TS" -ge "$DEADLINE_TS" ]; then
    echo "Retry timeout reached (5h). Stopping monitor."
    break
  fi

  INTERVAL=$(( 180 * (2 ** RETRY_COUNT) ))
  REMAINING=$(( DEADLINE_TS - NOW_TS ))
  if [ "$INTERVAL" -gt "$REMAINING" ]; then
    INTERVAL="$REMAINING"
  fi

  if tmux has-session -t "$SESSION" 2>/dev/null; then
    OUTPUT="$(tmux capture-pane -t "$SESSION" -p -S -120 2>/dev/null)" || {
      echo "tmux session $SESSION disappeared. Stopping."
      break
    }
    RECENT="$(printf '%s\n' "$OUTPUT" | tail -n 40)"

    if printf '%s\n' "$RECENT" | grep -q "__TASK_DONE__"; then
      echo "Task completed normally."
      break
    fi

    PROMPT_BACK=0
    EXIT_HINT=0
    LAST_LINE="$(printf '%s\n' "$RECENT" | grep -v '^$' | tail -n 1)"
    printf '%s\n' "$LAST_LINE" | grep -Eq '^[^[:space:]]*[$%#>] $' && PROMPT_BACK=1
    printf '%s\n' "$RECENT" | grep -Eiq '(exit code [0-9]|exited with|exit status [1-9])' && EXIT_HINT=1

    if [ "$PROMPT_BACK" -eq 1 ] || [ "$EXIT_HINT" -eq 1 ]; then
      RETRY_COUNT=$(( RETRY_COUNT + 1 ))

      case "$AGENT" in
        codex)
          if [ -s "$CODEX_SESSION_FILE" ]; then
            CODEX_SESSION_ID="$(cat "$CODEX_SESSION_FILE")"
            if ! printf '%s' "$CODEX_SESSION_ID" | grep -Eq '^[A-Za-z0-9_-]+$'; then
              echo "Invalid Codex session ID format"
              break
            fi
            echo "Crash detected. Resuming Codex session $CODEX_SESSION_ID (retry #$RETRY_COUNT)"
            tmux send-keys -t "$SESSION" "codex exec resume ${CODEX_SESSION_ID} \"Continue the previous task\"" Enter
          else
            echo "Missing Codex session ID file: $CODEX_SESSION_FILE"
            break
          fi
          ;;
        claude)
          echo "Crash detected. Resuming Claude Code (retry #$RETRY_COUNT)"
          tmux send-keys -t "$SESSION" 'claude --resume' Enter
          ;;
        opencode)
          echo "Crash detected. Resuming OpenCode (retry #$RETRY_COUNT)"
          tmux send-keys -t "$SESSION" 'opencode run "Continue"' Enter
          ;;
        pi)
          echo "Pi has no resume command. Manual restart required."
          break
          ;;
      esac
    else
      RETRY_COUNT=0
      INTERVAL=180
    fi
  else
    echo "tmux session $SESSION no longer exists. Stopping."
    break
  fi
  sleep "$INTERVAL"
done
