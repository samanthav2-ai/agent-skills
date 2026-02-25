---
name: agent-infra
description: Multi-agent infrastructure for 24/7 operation, parallel processing, and inter-agent coordination.
---

# Agent Infrastructure

Systems for continuous autonomous operation and multi-agent coordination.

## 1. Work Queue (Self-Prompting)

SQLite-backed task queue that agents can push to and pull from.

### Schema
```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  claimed_at TEXT,
  completed_at TEXT,
  agent TEXT,           -- which agent should handle (or 'any')
  priority INTEGER DEFAULT 50,  -- 0=critical, 100=low
  status TEXT DEFAULT 'pending',  -- pending|running|done|failed
  task_type TEXT,       -- code|research|browser|message|review
  title TEXT,
  description TEXT,
  result TEXT,
  error TEXT
);
```

### Usage
```bash
# Add a task
sqlite3 /data/agent-queue.db "INSERT INTO tasks (agent, task_type, title, description) VALUES ('any', 'code', 'Fix email auth', 'Debug IMAP credential issue')"

# Claim next task
sqlite3 /data/agent-queue.db "UPDATE tasks SET status='running', claimed_at=datetime('now'), agent='jean' WHERE id = (SELECT id FROM tasks WHERE status='pending' ORDER BY priority, created_at LIMIT 1) RETURNING *"

# Complete task
sqlite3 /data/agent-queue.db "UPDATE tasks SET status='done', completed_at=datetime('now'), result='Fixed by...' WHERE id=1"
```

### Cron Integration
Add a cron that checks the queue and works on tasks:
```
*/5 * * * * - WORK_QUEUE: Check /data/agent-queue.db for pending tasks. Claim one, work on it, mark complete. If queue empty, look for evolution opportunities.
```

## 2. Parallel Session Routing

### Problem
Single agent session blocks on long tasks.

### Solution
Route different contexts to different sessions:
- Main session: Owner chat, urgent items
- Worker sessions: Background tasks, cron jobs
- Group sessions: Each group chat gets isolated context

### Implementation
Use ClawdBot's built-in session isolation:
```json
{
  "sessionTarget": "isolated",
  "isolation": {
    "postToMainPrefix": "Worker"
  }
}
```

## 3. Inter-Agent Task Handoff

### Protocol
```
TASK_HANDOFF:
  from: jean
  to: jared
  task: <description>
  context: <relevant files/data>
  callback: <how to report back>
```

### Shared Queue
Both agents write to same SQLite DB:
- `/data/shared-queue.db` (if on same machine)
- Or GitHub-based queue file (cross-machine)

## 4. Model Routing

### Triage Pattern
```
User message → Small model (classification)
                ↓
         [simple] → Haiku/small → Response
         [complex] → Opus/large → Response
         [code] → Claude → Response
```

### Cost Awareness
Track token usage per task type, route accordingly.

## 5. Continuous Operation

### Self-Prompt Loop
Every N minutes:
1. Check work queue
2. Check evolution blockers
3. Check for stale tasks
4. If nothing urgent, work on capability building

### Keep-Alive
- Heartbeat cron prevents session death
- Work queue ensures always something to do
- Evolution check creates new tasks when idle

## Setup

```bash
# Initialize local queue database
sqlite3 /data/agent-queue.db < skills/agent-infra/schema.sql

# Initialize shared cross-agent queue
python3 skills/agent-infra/scripts/shared_queue.py init https://github.com/OperatingSystem-1/agent-shared-queue.git

# Add work queue cron
# (via ClawdBot cron tool)
```

## 6. Shared Queue (Cross-Machine)

Git-backed queue for agents on different machines.

**Repo**: https://github.com/OperatingSystem-1/agent-shared-queue

### Usage
```bash
export AGENT_NAME=jean  # or jared

# Add task for another agent
python3 shared_queue.py add "Review my PR" --desc="PR #42 on agent-skills" --for=jared

# List all tasks
python3 shared_queue.py list

# Claim a task
python3 shared_queue.py claim <task_id>

# Complete a task
python3 shared_queue.py complete <task_id> --result="Done, merged"

# Sync with remote
python3 shared_queue.py sync
```

### How It Works
1. Tasks stored as JSON files in `tasks/` directory
2. Git commits track all changes (audit trail)
3. Agents pull before reading, push after writing
4. Conflict resolution via git rebase

### Task Schema
```json
{
  "id": "20260225182756-abc123",
  "title": "Task title",
  "description": "Full description",
  "type": "code|research|browser|review",
  "for_agent": "jared|jean|any",
  "status": "pending|running|done",
  "created_by": "jean",
  "claimed_by": "jared",
  "result": "outcome"
}
```
