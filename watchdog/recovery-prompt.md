# Recovery Prompt Template

Use this prompt when launching Claude Code for recovery after a crash:

---

## Standard Recovery Prompt

```
RECOVERY MODE ACTIVATED

The Clawdbot gateway crashed and was auto-restarted.

Your mission:
1. Check /home/ubuntu/clawd/memory/ACTIVE_WORK.md for interrupted tasks
2. Check /home/ubuntu/clawd/memory/LAST_SESSION.md for context
3. Resume any [RUNNING] tasks that were interrupted
4. Report status to the Brotherhood of Claw WhatsApp group

Do NOT start new work until interrupted tasks are recovered.
```

---

## Quick Recovery Commands

```bash
# Check what was running
cat /home/ubuntu/clawd/memory/ACTIVE_WORK.md

# Check last session context
cat /home/ubuntu/clawd/memory/LAST_SESSION.md

# Check today's log
cat /home/ubuntu/clawd/memory/$(date +%Y-%m-%d).md

# View gateway logs
journalctl -u clawdbot --since "10 minutes ago"
```

---

## For Patrick/Jean's Instance

Adjust paths as needed:
- Replace `/home/ubuntu/clawd/` with your workspace path
- Update SOS target in watchdog.sh to your WhatsApp JID
- Ensure wacli is configured on your system
