---
name: model-router
description: Intelligent model routing - triage with small model, execute with capable one. Reduce costs while maintaining quality.
---

# Model Router Skill

Route tasks to appropriate models based on complexity.

## Concept

Not every task needs Claude Opus. Many can be handled by smaller, faster, cheaper models.

```
User Request → Triage (small model) → Route → Execute (appropriate model)
                   ↓
              [simple] → Haiku / small
              [code] → Claude / Codex
              [research] → Perplexity / Search + small
              [complex] → Opus / large
```

## Task Categories

| Category | Indicators | Recommended Model |
|----------|-----------|-------------------|
| **Simple** | Factual lookup, formatting, simple math | Haiku, GPT-4o-mini |
| **Code** | Code review, debugging, generation | Claude Sonnet, Codex |
| **Research** | Multi-source info gathering | Search + synthesis |
| **Complex** | Reasoning, planning, multi-step | Opus, GPT-4o |
| **Creative** | Writing, brainstorming | Sonnet, Claude |

## Implementation Options

### Option 1: ClawdBot Session Model Override
```bash
# Set model for current session
/model anthropic/claude-sonnet-4-5

# Or via session_status tool
session_status --model=anthropic/claude-sonnet-4-5
```

### Option 2: Config-Based Routing
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-5",
        routing: {
          "simple": "anthropic/claude-haiku-3-5",
          "code": "anthropic/claude-sonnet-4-5",
          "default": "anthropic/claude-opus-4-5"
        }
      }
    }
  }
}
```

### Option 3: Triage Prompt (Current Approach)
When you receive a task, quickly classify it:

```
TASK CLASSIFICATION:
- Is this a simple lookup or fact? → Use quick response, don't overthink
- Is this code-related? → Focus on code quality
- Does this require deep reasoning? → Take time, use full capability
- Is this research? → Use web_fetch, structured search
```

## Cost Awareness

| Model | Input $/1M | Output $/1M | Use Case |
|-------|-----------|-------------|----------|
| Haiku | $0.25 | $1.25 | Quick lookups, formatting |
| Sonnet | $3 | $15 | Balanced tasks, code |
| Opus | $15 | $75 | Complex reasoning |

A 10x cost difference means routing matters for high-volume agents.

## Self-Assessment Pattern

Before responding, ask:
1. **Complexity**: Does this need deep thinking or is it straightforward?
2. **Stakes**: What's the cost of a suboptimal answer?
3. **Speed**: Is quick response more valuable than perfect?

Adjust effort accordingly — don't use a sledgehammer on a thumbtack.

## Integration with Work Queue

The agent-infra work queue includes `task_type`:
- `general` → Default model
- `code` → Code-optimized
- `research` → Search + synthesis
- `review` → Quality check
- `verify` → Double-check prior work

Workers can auto-select model based on task type.

## Future: Actual Routing Implementation

When ClawdBot supports model routing at the gateway level:
1. Classify incoming message
2. Route to appropriate model endpoint
3. Track cost/quality metrics
4. Adjust routing based on outcomes

For now, this is a skill for self-awareness about model selection.
