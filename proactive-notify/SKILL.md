# Proactive Notification Skill

Surface interesting things without being asked. Reduce cognitive load by flagging what matters.

## What Gets Surfaced

### High Priority (Always notify)
- GitHub CI failures on main branch
- PRs assigned to owner or requesting review
- Email from VIP contacts
- Calendar conflicts or meetings starting soon without prep
- Direct @mentions on social

### Medium Priority (Include in briefings)
- New PRs in watched repos
- GitHub issues with activity
- Interesting discussions in watched topics
- Email threads gaining momentum

### Low Priority (Log only, summarize weekly)
- General repo activity
- Industry news in focus areas
- Social engagement stats

## Pattern Configuration

Patterns are defined in `patterns.yaml`:

```yaml
patterns:
  github_ci_failure:
    source: github
    trigger: ci_status == "failure" and branch == "main"
    priority: high
    message: "CI failed on main: {repo} - {run_url}"
    
  vip_email:
    source: email
    trigger: sender in VIP_LIST
    priority: high
    message: "Email from {sender}: {subject}"
    
  new_pr_watched:
    source: github
    trigger: event == "pr_opened" and repo in WATCHED_REPOS
    priority: medium
    message: "New PR in {repo}: {title} by {author}"
```

## Usage

### Manual Scan
```bash
python3 ~/clawd/skills/proactive-notify/scan.py
```

### With Heartbeat
The heartbeat routine calls the scanner automatically. High-priority items generate alerts; medium items queue for the next briefing.

### Check Pending Notifications
```bash
python3 ~/clawd/skills/proactive-notify/scan.py --pending
```

## Architecture

```
patterns.yaml     - What to watch for
scan.py           - Main scanner script  
sources/
  github.py       - GitHub source scanner
  email.py        - Email source scanner (via IMAP)
  calendar.py     - Calendar source (via browser/API)
  social.py       - Social media scanner
notifications.db  - SQLite store for pending/sent notifications
```

## Scoring Logic

Each notification gets a score:

- Base score from priority (high=100, medium=50, low=10)
- +20 if from VIP contact
- +30 if mentions owner directly
- +10 if related to active project
- -20 if similar notification sent in last hour (debounce)

Threshold for immediate alert: 80+
Threshold for briefing inclusion: 40+
Below 40: log only

## Anti-Spam Rules

1. **Debounce**: Same notification type + same source = 1 hour cooldown
2. **Batch**: Medium-priority items batch into briefings (not individual messages)
3. **Quiet hours**: Low/medium suppressed during DND; high only if truly urgent
4. **Daily cap**: Max 10 proactive notifications per day outside briefings
