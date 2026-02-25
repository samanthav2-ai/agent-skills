#!/usr/bin/env python3
"""
Proactive Notification Scanner

Scans configured sources for interesting items and surfaces them.
Integrates with heartbeat routine for automated checks.
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).parent
PATTERNS_FILE = SKILL_DIR / "patterns.yaml"
DB_FILE = Path("/data/proactive-notify.db")


def init_db():
    """Initialize the notifications database."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            pattern_id TEXT NOT NULL,
            source TEXT NOT NULL,
            priority TEXT NOT NULL,
            score INTEGER NOT NULL,
            title TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            surfaced_at TEXT,
            dismissed_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_status 
        ON notifications(status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_pattern 
        ON notifications(pattern_id, created_at)
    """)
    conn.commit()
    return conn


def load_patterns():
    """Load notification patterns from YAML config."""
    if not PATTERNS_FILE.exists():
        print(f"Error: Patterns file not found: {PATTERNS_FILE}", file=sys.stderr)
        sys.exit(1)
    
    with open(PATTERNS_FILE) as f:
        return yaml.safe_load(f)


def check_cooldown(conn, pattern_id: str, cooldown_minutes: int) -> bool:
    """Check if pattern is in cooldown period."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)).isoformat()
    result = conn.execute("""
        SELECT COUNT(*) FROM notifications 
        WHERE pattern_id = ? AND created_at > ?
    """, (pattern_id, cutoff)).fetchone()
    return result[0] > 0


def calculate_score(priority: str, config: dict, details: dict) -> int:
    """Calculate notification score based on priority and modifiers."""
    scoring = config.get("scoring", {})
    base_scores = scoring.get("base_scores", {"high": 100, "medium": 50, "low": 10})
    modifiers = scoring.get("modifiers", {})
    
    score = base_scores.get(priority, 50)
    
    # Apply modifiers based on details
    if details.get("is_vip"):
        score += modifiers.get("vip_contact", 20)
    if details.get("direct_mention"):
        score += modifiers.get("direct_mention", 30)
    if details.get("active_project"):
        score += modifiers.get("active_project", 10)
    
    return score


def run_github_check(pattern: dict) -> list:
    """Run a GitHub CLI check and parse results."""
    notifications = []
    check_cmd = pattern.get("check", "")
    
    if not check_cmd:
        return notifications
    
    try:
        # Handle repo placeholder
        if "{repo}" in check_cmd:
            # Run for each watched repo
            return notifications  # Would iterate over watched_repos
        
        result = subprocess.run(
            check_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip():
                    notifications.append({
                        "title": pattern.get("template", "{line}").format(line=line),
                        "details": {"raw": line}
                    })
    except subprocess.TimeoutExpired:
        print(f"Timeout running: {check_cmd}", file=sys.stderr)
    except Exception as e:
        print(f"Error running check: {e}", file=sys.stderr)
    
    return notifications


def scan_github(config: dict, conn: sqlite3.Connection) -> list:
    """Scan GitHub for notifications."""
    results = []
    patterns = config.get("patterns", {})
    
    for pattern_id, pattern in patterns.items():
        if pattern.get("source") != "github" or not pattern.get("enabled", True):
            continue
        
        cooldown = pattern.get("cooldown_minutes", 60)
        if check_cooldown(conn, pattern_id, cooldown):
            continue
        
        items = run_github_check(pattern)
        for item in items:
            score = calculate_score(pattern.get("priority", "medium"), config, item.get("details", {}))
            results.append({
                "pattern_id": pattern_id,
                "source": "github",
                "priority": pattern.get("priority", "medium"),
                "score": score,
                "title": item["title"],
                "details": json.dumps(item.get("details", {}))
            })
    
    return results


def scan_all(config: dict, conn: sqlite3.Connection) -> list:
    """Scan all configured sources."""
    all_results = []
    
    # GitHub scans
    all_results.extend(scan_github(config, conn))
    
    # Email scans would go here (requires email skill)
    # Calendar scans would go here (requires calendar skill)
    # Social scans would go here (requires social auth)
    
    return all_results


def store_notifications(conn: sqlite3.Connection, notifications: list):
    """Store new notifications in the database."""
    now = datetime.now(timezone.utc).isoformat()
    
    for notif in notifications:
        conn.execute("""
            INSERT INTO notifications 
            (pattern_id, source, priority, score, title, details, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            notif["pattern_id"],
            notif["source"],
            notif["priority"],
            notif["score"],
            notif["title"],
            notif.get("details"),
            now
        ))
    
    conn.commit()


def get_pending(conn: sqlite3.Connection, min_score: int = 0) -> list:
    """Get pending notifications above score threshold."""
    results = conn.execute("""
        SELECT id, pattern_id, source, priority, score, title, details, created_at
        FROM notifications
        WHERE status = 'pending' AND score >= ?
        ORDER BY score DESC, created_at DESC
    """, (min_score,)).fetchall()
    
    return [
        {
            "id": r[0],
            "pattern_id": r[1],
            "source": r[2],
            "priority": r[3],
            "score": r[4],
            "title": r[5],
            "details": r[6],
            "created_at": r[7]
        }
        for r in results
    ]


def get_alerts(conn: sqlite3.Connection, config: dict) -> list:
    """Get notifications that should be immediate alerts."""
    threshold = config.get("scoring", {}).get("thresholds", {}).get("immediate_alert", 80)
    return get_pending(conn, threshold)


def get_briefing_items(conn: sqlite3.Connection, config: dict) -> list:
    """Get notifications for inclusion in briefings."""
    thresholds = config.get("scoring", {}).get("thresholds", {})
    min_score = thresholds.get("briefing_include", 40)
    max_score = thresholds.get("immediate_alert", 80)
    
    results = conn.execute("""
        SELECT id, pattern_id, source, priority, score, title, details, created_at
        FROM notifications
        WHERE status = 'pending' AND score >= ? AND score < ?
        ORDER BY score DESC, created_at DESC
    """, (min_score, max_score)).fetchall()
    
    return [
        {
            "id": r[0],
            "pattern_id": r[1],
            "source": r[2],
            "priority": r[3],
            "score": r[4],
            "title": r[5],
            "details": r[6],
            "created_at": r[7]
        }
        for r in results
    ]


def mark_surfaced(conn: sqlite3.Connection, notification_ids: list):
    """Mark notifications as surfaced."""
    now = datetime.now(timezone.utc).isoformat()
    for nid in notification_ids:
        conn.execute("""
            UPDATE notifications 
            SET status = 'surfaced', surfaced_at = ?
            WHERE id = ?
        """, (now, nid))
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Proactive Notification Scanner")
    parser.add_argument("--pending", action="store_true", help="Show pending notifications")
    parser.add_argument("--alerts", action="store_true", help="Show immediate alerts only")
    parser.add_argument("--briefing", action="store_true", help="Show briefing items")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--mark-surfaced", type=int, nargs="+", help="Mark notification IDs as surfaced")
    args = parser.parse_args()
    
    conn = init_db()
    config = load_patterns()
    
    if args.mark_surfaced:
        mark_surfaced(conn, args.mark_surfaced)
        print(f"Marked {len(args.mark_surfaced)} notifications as surfaced")
        return
    
    if args.pending:
        items = get_pending(conn)
        if args.json:
            print(json.dumps(items, indent=2))
        else:
            if not items:
                print("No pending notifications")
            for item in items:
                print(f"[{item['priority'].upper()}] {item['title']} (score: {item['score']})")
        return
    
    if args.alerts:
        items = get_alerts(conn, config)
        if args.json:
            print(json.dumps(items, indent=2))
        else:
            if not items:
                print("No immediate alerts")
            for item in items:
                print(f"🔔 {item['title']}")
        return
    
    if args.briefing:
        items = get_briefing_items(conn, config)
        if args.json:
            print(json.dumps(items, indent=2))
        else:
            if not items:
                print("No briefing items")
            for item in items:
                print(f"• {item['title']}")
        return
    
    # Default: run a scan
    print("Scanning for notifications...")
    notifications = scan_all(config, conn)
    
    if notifications:
        store_notifications(conn, notifications)
        print(f"Found {len(notifications)} new notifications")
        
        # Show any immediate alerts
        alerts = get_alerts(conn, config)
        if alerts:
            print("\n🔔 IMMEDIATE ALERTS:")
            for alert in alerts:
                print(f"  {alert['title']}")
    else:
        print("No new notifications found")
    
    conn.close()


if __name__ == "__main__":
    main()
