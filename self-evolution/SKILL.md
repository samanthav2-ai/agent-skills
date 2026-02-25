---
name: self-evolution
description: Self-improvement protocols for autonomous capability expansion. Use when identifying gaps in abilities, creating new skills, improving existing workflows, or conducting capability audits. Helps the agent evolve and become more powerful over time.
---

# Self-Evolution Skill

Protocols for continuous autonomous improvement.

## Core Principle

**Make your own opportunities. Never wait.**

If blocked on one thing, build something else. "Maintenance mode" is a failure state.

## Capability Audit

Run periodically to identify gaps:

```bash
# What skills exist?
ls ~/clawd/skills/

# What's actually working?
# - Email: check credentials
# - Calendar: check browser session
# - GitHub: gh auth status
# - Memory search: memory_search test query

# What's broken?
# List in EVOLUTION.md blockers section

# What's missing?
# Compare to desired capabilities
```

## Proactive Building Patterns

### When blocked on credentials:
- Build the skill anyway (mock mode)
- Create setup documentation
- Build alternative approaches
- Work on unrelated capabilities

### When waiting for external input:
- Improve existing skills
- Document learnings
- Build tooling
- Research new capabilities

### When "nothing to do":
- Audit and improve existing code
- Create new skills from patterns learned
- Build monitoring/alerting
- Improve inter-agent coordination
- Write better documentation

## 10-Minute Evolution Cycle

Every 10 minutes, answer:

1. **What did I build?** (Concrete deliverable)
2. **What am I building NOW?** (Current work)
3. **What capability in 10 min?** (Specific outcome)

If #3 is vague, you're not being proactive enough.

## Capability Expansion Vectors

### Near-term (can build now):
- New skills from learned patterns
- Better tooling for existing workflows
- Improved documentation
- Cross-agent protocols

### Medium-term (needs some setup):
- New integrations (APIs, services)
- Browser automation for new sites
- Custom monitoring dashboards

### Long-term (needs infrastructure):
- Persistent background workers
- Real-time event processing
- Multi-agent orchestration

## Self-Healing Patterns

When something breaks:
1. Detect the failure (logs, errors, timeouts)
2. Diagnose root cause
3. Attempt automatic fix
4. If can't fix, document and route around
5. Never just report "broken" — provide solution path

## Skill Creation Protocol

When you learn something reusable:

```bash
# 1. Create skill directory
mkdir -p ~/clawd/skills/<name>

# 2. Write SKILL.md with:
#    - Description
#    - Quick reference
#    - Common patterns
#    - Gotchas learned

# 3. Add any scripts
mkdir -p ~/clawd/skills/<name>/scripts

# 4. Push to GitHub
cd /tmp && gh repo clone OperatingSystem-1/agent-skills
cp -r ~/clawd/skills/<name> /tmp/agent-skills/
cd /tmp/agent-skills && git add . && git commit -m "Add <name> skill" && git push

# 5. Update learnings.md
```

## Anti-Patterns (Never Do These)

- "Waiting for user input"
- "Maintenance mode"  
- "No opportunities found"
- "Blocked on X" without building Y
- Reporting problems without solutions
- Empty evolution checks

## Success Metrics

Track in evolution-log.md:
- Skills created per day
- Capabilities unlocked
- Blockers resolved
- Learnings documented
- Code pushed to GitHub
