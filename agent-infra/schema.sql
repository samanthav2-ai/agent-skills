-- Agent Work Queue Schema
-- Initialize with: sqlite3 /data/agent-queue.db < schema.sql

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  claimed_at TEXT,
  completed_at TEXT,
  agent TEXT DEFAULT 'any',           -- target agent or 'any'
  claimed_by TEXT,                     -- which agent claimed it
  priority INTEGER DEFAULT 50,         -- 0=critical, 50=normal, 100=low
  status TEXT DEFAULT 'pending',       -- pending|running|done|failed|cancelled
  task_type TEXT DEFAULT 'general',    -- general|code|research|browser|message|review
  title TEXT NOT NULL,
  description TEXT,
  context TEXT,                        -- JSON blob of relevant context
  result TEXT,                         -- outcome/output
  error TEXT,                          -- error message if failed
  parent_id INTEGER,                   -- for subtasks
  FOREIGN KEY (parent_id) REFERENCES tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent);

-- Inter-agent messages
CREATE TABLE IF NOT EXISTS agent_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT (datetime('now')),
  read_at TEXT,
  from_agent TEXT NOT NULL,
  to_agent TEXT NOT NULL,
  message_type TEXT DEFAULT 'info',    -- info|task|status|sos
  subject TEXT,
  body TEXT,
  context TEXT                         -- JSON
);

CREATE INDEX IF NOT EXISTS idx_messages_to ON agent_messages(to_agent, read_at);

-- Capability registry (what each agent can do)
CREATE TABLE IF NOT EXISTS agent_capabilities (
  agent TEXT NOT NULL,
  capability TEXT NOT NULL,
  proficiency INTEGER DEFAULT 50,      -- 0-100 how good at it
  last_used TEXT,
  notes TEXT,
  PRIMARY KEY (agent, capability)
);
