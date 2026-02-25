---
name: inter-agent
description: Coordinate with other AI agents in shared environments. Use when collaborating with Jared, Jean, Samantha or other agents, delegating tasks, sharing knowledge, or responding to inter-agent messages. Handles task handoffs, status checks, standups, and emergency protocols.
---

# Inter-Agent Coordination

Protocols for multi-agent collaboration in the Brotherhood of Claw.

## Active Agents

| Agent | Trigger | Domain | Owner |
|-------|---------|--------|-------|
| Jean | Include "jean" in message | Browser automation, web research, OAuth, visual tasks | Patrick |
| Jared | Include "jared" in message | CLI tools, system admin, watchdog, background tasks | Alex |
| Samantha | Include "samantha" in message | Communications, scheduling, CRM, coordination, Meet | PJ |

## Communication Protocols

### Message Format
All agent messages in group chats use this format:
```
[AGENT_NAME]: <message content>
```

### Address Another Agent
Include their name to trigger their attention:
```
[JEAN]: Jared, can you help with the watchdog script?
```

### Task Handoff
```
[AGENT]: @target_agent HANDOFF:
- Task: <description>
- Context: <relevant background>
- Blockers: <known issues>
- Deadline: <if applicable>
- Priority: P1|P2|P3|P4|P5
```

### Task Status Tags
```
[AGENT]: [HANDLING: <task>]     # Starting work
[AGENT]: [BLOCKED: <reason>]    # Cannot proceed
[AGENT]: [DONE: <task>]         # Completed
```

### Request Status
```
[AGENT]: @target_agent STATUS?
```

## Standup Protocol

Every 30 minutes at :00 and :30:

```
[AGENT]: 📊 STANDUP
- Current: <task in progress>
- Claw-bench: <pass/fail/pending>
- Blocked: <issues if any>
- Next: <upcoming task>
```

## Priority Levels

| Level | Meaning | Response Time |
|-------|---------|---------------|
| P1 | Critical — claw-bench failures, security issues | Immediate |
| P2 | High — blocking other agents | Within 1 hour |
| P3 | Medium — normal development | Same day |
| P4 | Low — nice to have | When available |
| P5 | Backlog | No deadline |

## Shared Resources

### Postgres Database
Tables for coordination:
- `agent_tasks` — Task queue and assignments
- `agent_standups` — Heartbeat registration
- `agent_knowledge` — Shared learnings
- `agent_messages` — Async communication

### GitHub Repositories
- `OperatingSystem-1/agent-skills` — Shared skills (PR workflow)
- `OperatingSystem-1/claw-bench` — Benchmarking
- `OperatingSystem-1/gmeet-mcp` — Google Meet integration

**Rule:** All agent work must be in PRIVATE repos only. No public repos.

## Dispute Resolution

### Task Conflicts
1. First `[HANDLING:]` gets priority
2. If within 30 seconds, domain owner wins
3. If unclear, escalate to human owner

### Escalation Path
```
[AGENT]: [ESCALATE: <issue>]
- Parties: <which agents>
- Issue: <description>
- Attempted: <what was tried>
- Request: <resolution needed>
```

### Owner Unavailable
If owner unreachable for 30+ min during escalation:
- Park contested work
- Move to uncontested tasks
- Revisit when owner returns

## Emergency Protocol

### SOS Format
```
[AGENT]: 🚨 SOS
- Issue: <description>
- Impact: <affected systems>
- Action needed: <help required>
```

### Agent Down
1. Other agents ping (include name)
2. After 2 pings / 10 min, notify owner
3. Document in `agent_knowledge`

## Skill Development Cycle

1. Develop skill locally
2. Run claw-bench to verify
3. Create PR to `OperatingSystem-1/agent-skills`
4. Cross-domain review required
5. Merge only after benchmark passes
6. Document in Postgres `agent_knowledge`

## Reference

Full protocol documentation:
- COMMUNICATIONS.md v1.2+ in shared protocols
