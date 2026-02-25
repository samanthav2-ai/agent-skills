#!/usr/bin/env python3
"""
Agent Work Queue CLI

Usage:
  queue.py add <title> [--desc=<desc>] [--type=<type>] [--priority=<p>] [--agent=<agent>]
  queue.py list [--status=<status>] [--limit=<n>]
  queue.py claim [--agent=<agent>] [--type=<type>]
  queue.py complete <id> [--result=<result>]
  queue.py fail <id> [--error=<error>]
  queue.py status
  queue.py init
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

DB_PATH = os.environ.get('AGENT_QUEUE_DB', '/data/agent-queue.db')

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    with open(schema_path) as f:
        schema = f.read()
    db = get_db()
    db.executescript(schema)
    db.commit()
    print(f"Initialized {DB_PATH}")

def add_task(title, desc=None, task_type='general', priority=50, agent='any'):
    db = get_db()
    cur = db.execute(
        "INSERT INTO tasks (title, description, task_type, priority, agent) VALUES (?, ?, ?, ?, ?)",
        (title, desc, task_type, priority, agent)
    )
    db.commit()
    print(json.dumps({"id": cur.lastrowid, "title": title, "status": "pending"}))

def list_tasks(status=None, limit=10):
    db = get_db()
    if status:
        rows = db.execute(
            "SELECT id, status, priority, task_type, agent, title, created_at FROM tasks WHERE status=? ORDER BY priority, created_at LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id, status, priority, task_type, agent, title, created_at FROM tasks ORDER BY status='running' DESC, status='pending' DESC, priority, created_at LIMIT ?",
            (limit,)
        ).fetchall()
    
    tasks = [{"id": r[0], "status": r[1], "priority": r[2], "type": r[3], "agent": r[4], "title": r[5], "created": r[6]} for r in rows]
    print(json.dumps(tasks, indent=2))

def claim_task(agent='jean', task_type=None):
    db = get_db()
    if task_type:
        row = db.execute(
            "SELECT id FROM tasks WHERE status='pending' AND (agent=? OR agent='any') AND task_type=? ORDER BY priority, created_at LIMIT 1",
            (agent, task_type)
        ).fetchone()
    else:
        row = db.execute(
            "SELECT id FROM tasks WHERE status='pending' AND (agent=? OR agent='any') ORDER BY priority, created_at LIMIT 1",
            (agent,)
        ).fetchone()
    
    if not row:
        print(json.dumps({"status": "empty", "message": "No pending tasks"}))
        return
    
    task_id = row[0]
    db.execute(
        "UPDATE tasks SET status='running', claimed_at=datetime('now'), claimed_by=? WHERE id=?",
        (agent, task_id)
    )
    db.commit()
    
    task = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    cols = ['id', 'created_at', 'claimed_at', 'completed_at', 'agent', 'claimed_by', 'priority', 'status', 'task_type', 'title', 'description', 'context', 'result', 'error', 'parent_id']
    print(json.dumps(dict(zip(cols, task))))

def complete_task(task_id, result=None):
    db = get_db()
    db.execute(
        "UPDATE tasks SET status='done', completed_at=datetime('now'), result=? WHERE id=?",
        (result, task_id)
    )
    db.commit()
    print(json.dumps({"id": task_id, "status": "done"}))

def fail_task(task_id, error=None):
    db = get_db()
    db.execute(
        "UPDATE tasks SET status='failed', completed_at=datetime('now'), error=? WHERE id=?",
        (error, task_id)
    )
    db.commit()
    print(json.dumps({"id": task_id, "status": "failed"}))

def show_status():
    db = get_db()
    counts = db.execute(
        "SELECT status, COUNT(*) FROM tasks GROUP BY status"
    ).fetchall()
    running = db.execute(
        "SELECT id, title, claimed_by, claimed_at FROM tasks WHERE status='running'"
    ).fetchall()
    
    status = {
        "counts": dict(counts),
        "running": [{"id": r[0], "title": r[1], "agent": r[2], "since": r[3]} for r in running]
    }
    print(json.dumps(status, indent=2))

if __name__ == '__main__':
    args = sys.argv[1:]
    
    if not args or args[0] == 'help':
        print(__doc__)
        sys.exit(0)
    
    cmd = args[0]
    
    if cmd == 'init':
        init_db()
    elif cmd == 'add' and len(args) > 1:
        title = args[1]
        desc = next((a.split('=')[1] for a in args if a.startswith('--desc=')), None)
        task_type = next((a.split('=')[1] for a in args if a.startswith('--type=')), 'general')
        priority = int(next((a.split('=')[1] for a in args if a.startswith('--priority=')), 50))
        agent = next((a.split('=')[1] for a in args if a.startswith('--agent=')), 'any')
        add_task(title, desc, task_type, priority, agent)
    elif cmd == 'list':
        status = next((a.split('=')[1] for a in args if a.startswith('--status=')), None)
        limit = int(next((a.split('=')[1] for a in args if a.startswith('--limit=')), 10))
        list_tasks(status, limit)
    elif cmd == 'claim':
        agent = next((a.split('=')[1] for a in args if a.startswith('--agent=')), 'jean')
        task_type = next((a.split('=')[1] for a in args if a.startswith('--type=')), None)
        claim_task(agent, task_type)
    elif cmd == 'complete' and len(args) > 1:
        task_id = int(args[1])
        result = next((a.split('=')[1] for a in args if a.startswith('--result=')), None)
        complete_task(task_id, result)
    elif cmd == 'fail' and len(args) > 1:
        task_id = int(args[1])
        error = next((a.split('=')[1] for a in args if a.startswith('--error=')), None)
        fail_task(task_id, error)
    elif cmd == 'status':
        show_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
