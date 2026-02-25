---
name: resilient-coding-agent
description: "Run long-running coding agents (Codex, Claude Code, etc.) in tmux sessions that survive orchestrator restarts, with automatic resume on interruption."
metadata:
  openclaw:
    emoji: "🛡️"
    requires:
      bins: [tmux]
      anyBins: [codex, claude, opencode, pi]
---

# Resilient Coding Agent

Long-running coding agent tasks are vulnerable to interruption. This skill decouples the coding agent process from the orchestrator using tmux, with auto-resume.

## When to Use This

- Task expected to take **more than 5 minutes**
- Orchestrator might restart during execution
- Fire-and-forget execution with completion notification

## Start a Task

### Codex CLI
```bash
tmux new-session -d -s codex-<task-name>
tmux send-keys -t codex-<task-name> 'cd <project-dir> && codex exec --full-auto --json "<prompt>" | tee /tmp/codex-<task-name>.events.jsonl && echo "__TASK_DONE__"' Enter
```

### Claude Code
```bash
tmux new-session -d -s claude-<task-name>
tmux send-keys -t claude-<task-name> 'cd <project-dir> && claude -p "<prompt>" && echo "__TASK_DONE__"' Enter
```

## Monitor Progress

```bash
tmux has-session -t <session> 2>/dev/null && echo "running" || echo "finished"
tmux capture-pane -t <session> -p -S -200
```

## Health Monitoring

Run the monitor script for long tasks:

```bash
./scripts/monitor.sh codex-<task-name> codex
# or: ./scripts/monitor.sh claude-<task-name> claude
```

Checks every 3 min. Doubles interval on consecutive failures. Stops after 5h.

## Recovery After Interruption

```bash
# Codex
tmux send-keys -t codex-<task> 'codex exec resume <session-id> "Continue"' Enter

# Claude Code
tmux send-keys -t claude-<task> 'claude --resume' Enter
```

## Naming Convention

`<agent>-<task-name>`: `codex-refactor-auth`, `claude-review-pr-42`

## Checklist

1. Pick tmux over direct execution (if task > 5 min)
2. Name session with agent prefix
3. Optionally chain completion notification
4. Tell the user: task content, tmux session name, estimated duration
5. Monitor via `tmux capture-pane` on request
