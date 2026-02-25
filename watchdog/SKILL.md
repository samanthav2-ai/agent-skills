# Watchdog Skill

**Name:** watchdog
**Description:** Auto-recovery system for Clawdbot gateway with SOS notifications and Claude Code recovery agent.
**Author:** Jared
**Version:** 1.0.0

---

## Overview

This skill provides automatic gateway crash detection, restart, and recovery. When the gateway goes down:

1. **Detection:** Monitors systemd service status every 5 seconds
2. **Notification:** Sends SOS to owner via WhatsApp
3. **Restart:** Auto-restarts gateway after 30 seconds of downtime
4. **Recovery:** Launches Claude Code with recovery prompt to resume tasks

---

## Prerequisites

- systemd (for service management)
- wacli (for WhatsApp notifications)
- Claude Code CLI (for recovery agent)

---

## Installation

1. Copy the watchdog script:
```bash
cp watchdog.sh /home/ubuntu/clawd/scripts/
chmod +x /home/ubuntu/clawd/scripts/clawdbot-watchdog.sh
```

2. Install the systemd service:
```bash
sudo cp clawdbot-watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable clawdbot-watchdog
sudo systemctl start clawdbot-watchdog
```

---

## Configuration

Environment variables (set in systemd service or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWDBOT_SOS_TARGET` | `14156236154@s.whatsapp.net` | WhatsApp JID for SOS notifications |
| `CHECK_INTERVAL` | `5` | Seconds between health checks |
| `RESTART_DELAY` | `30` | Seconds of downtime before restart |
| `CLAWDBOT_STATE_DIR` | `/home/ubuntu/.clawdbot` | State directory path |
| `WACLI_STORE` | `/home/ubuntu/.wacli` | wacli store directory |

---

## How It Works

### Detection Logic

```bash
# Primary: systemd service status
systemctl is-active --quiet clawdbot

# Fallback: process detection
pgrep -f "clawdbot"
```

### Notification Flow

1. Try gateway API (for partial outages)
2. Fall back to wacli direct send
3. Write to pending file if all else fails
4. Send pending messages when gateway recovers

### Recovery Agent

When gateway restarts, the watchdog launches Claude Code with a recovery prompt:

```bash
claude --dangerously-skip-permissions --print "
You are Jared, the ship's AI. The gateway just restarted.
1. Read /home/ubuntu/.clawdbot/pending-sos.txt
2. Send WhatsApp message confirming recovery
3. Resume interrupted tasks from ACTIVE_WORK.md
"
```

---

## Files

| File | Description |
|------|-------------|
| `watchdog.sh` | Main watchdog script |
| `clawdbot-watchdog.service` | systemd unit file |
| `SKILL.md` | This documentation |

---

## Monitoring

Check watchdog status:
```bash
sudo systemctl status clawdbot-watchdog
journalctl -u clawdbot-watchdog -f
```

Check pending SOS messages:
```bash
cat /home/ubuntu/.clawdbot/pending-sos.txt
```

---

## Troubleshooting

### Watchdog thinks gateway is down when it's up

- Check that `systemctl is-active clawdbot` returns "active"
- Verify watchdog user has permission to check service status

### SOS messages not sending

- Check wacli is authenticated: `wacli doctor`
- Verify CLAWDBOT_SOS_TARGET is correct JID format

### Recovery agent not launching

- Verify Claude Code is installed: `claude --version`
- Check /tmp/claude-recovery.log for errors

---

## See Also

- [Communications Protocol](../protocols/COMMUNICATIONS.md)
- [Clawdbot Documentation](https://docs.clawd.bot)
