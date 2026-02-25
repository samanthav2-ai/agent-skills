---
name: clawd-cursor
description: Desktop/browser automation via ClawdCursor API. Send natural language tasks to control browser and desktop apps.
---

# ClawdCursor Skill

AI desktop agent — control browser and apps via natural language tasks.

## Quick Start

```bash
# Start ClawdCursor (uses Ollama + Playwright)
bash ~/clawd/skills/clawd-cursor/start.sh
```

## Capabilities by Platform

| Feature | Linux (headless) | Windows | macOS |
|---------|-----------------|---------|-------|
| Browser automation (Playwright) | ✅ Full | ✅ Full | ✅ Full |
| URL navigation | ✅ | ✅ | ✅ |
| Form filling | ✅ | ✅ | ✅ |
| Screenshots | ✅ | ✅ | ✅ |
| Native desktop (mouse/keyboard) | ⚠️ Xvfb | ✅ | ✅ |
| Accessibility tree reasoning | ❌ | ✅ | ✅ |
| LLM planning (Ollama) | ✅ | ✅ | ✅ |

**Linux Note**: Browser automation via Playwright works perfectly. Native desktop (Start menu, app switching) works in Xvfb but has limited accessibility APIs.

## API Endpoints

ClawdCursor runs at `http://127.0.0.1:3847`:

### Send a Task
```bash
curl -s -X POST http://127.0.0.1:3847/task \
  -H "Content-Type: application/json" \
  -d '{"task": "Navigate to https://github.com"}'
```

### Check Status
```bash
curl -s http://127.0.0.1:3847/status
```

### Confirm Safety-Gated Actions
```bash
curl -s -X POST http://127.0.0.1:3847/confirm \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### Abort Task
```bash
curl -s -X POST http://127.0.0.1:3847/abort
```

## Task Examples

### Browser Tasks (Works Great on Linux)

| Task | Example |
|------|---------|
| Navigate | `Navigate to https://example.com` |
| Search | `Go to google.com and search for AI news` |
| Fill form | `Go to example.com/form and fill name=John, email=john@test.com` |
| Click element | `Click the Sign In button` |
| Type text | `Type "hello world" in the search box` |

### Desktop Tasks (Works on Windows/macOS)

| Task | Example |
|------|---------|
| Launch app | `Open Chrome` |
| Keyboard | `Press Ctrl+C` |
| Window management | `Minimize all windows` |

## Pipeline Architecture

```
Layer 0: Browser (Playwright)        → URL detection → instant ✅
Layer 1: Action Router (regex)       → Pattern matching → instant ✅  
Layer 1.5: Smart Interaction         → CDP + UI automation + 1 LLM call
Layer 2: A11y Reasoner (Ollama)      → Text-only LLM reasoning
Layer 3: Vision (requires API key)   → Screenshot → vision LLM
```

On Linux headless: Layers 0-1 work best. Layer 1.5+ have limited accessibility support.

## Local LLM Setup (Ollama)

ClawdCursor uses Ollama for LLM reasoning:

```bash
# Verify Ollama is running
curl -s http://localhost:11434/api/version

# Model: qwen2.5:3b (pre-configured)
OLLAMA_MODELS=/data/ollama/models /data/ollama/bin/ollama list
```

Config stored in: `~/clawd/clawd-cursor/.clawd-config.json`

## Integration with ClawdBot

ClawdCursor complements ClawdBot's built-in browser tool:

- **ClawdBot browser tool**: Fine-grained Playwright control (snapshots, ref-based clicks)
- **ClawdCursor**: Natural language goals ("navigate to X and fill the form")

Use ClawdCursor when you want to describe a goal in natural language rather than individual actions.

## Troubleshooting

### Check if running
```bash
curl -s http://127.0.0.1:3847/status
```

### View logs
```bash
tail -f /tmp/clawd-cursor.log
```

### Restart
```bash
pkill -f "clawd-cursor"
bash ~/clawd/skills/clawd-cursor/start.sh
```

### Common issues

1. **"Could not open main display"** - Run with xvfb-run or set DISPLAY
2. **"Accessibility script error"** - Normal on Linux; browser automation still works
3. **Port in use** - Kill existing process: `pkill -f "node dist/index.js"`

## Learnings & Gotchas

### Linux Headless Setup (Xvfb)
**Problem**: ClawdCursor needs a display, but headless Linux has none.
**Solution**: Use `xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24"` to create a virtual framebuffer.
**Gotcha**: Accessibility APIs are limited in Xvfb — Layer 2+ reasoning may not work as well as on real displays with full a11y support. Browser automation (Playwright) works perfectly though.

### Ollama Integration
**Pattern**: ClawdCursor uses local Ollama for LLM reasoning. On resource-constrained systems:
- Use smaller models (qwen2.5:3b works well)
- Set `OLLAMA_MODELS` to a data partition with space
- Verify Ollama is running before starting ClawdCursor

### Task Granularity
**Learning**: ClawdCursor works best with goal-oriented tasks, not micro-instructions.
- ✅ Good: "Go to github.com and search for clawdbot"
- ❌ Less good: "Click the search box, type clawdbot, press enter"

The LLM planner breaks down goals into steps — let it do its job.

### When to Use ClawdCursor vs ClawdBot Browser Tool
- **ClawdCursor**: Natural language goals, multi-step workflows, when you don't know the exact steps
- **ClawdBot browser**: Precise control, snapshot + ref-based clicking, when you need specific element interaction
