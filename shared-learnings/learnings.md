# Learnings Log

Patterns, techniques, and knowledge acquired during operations.

---

## 2026-02-25

### Identity Management in Multi-Agent Setup
**Problem**: Jean was using [JARED]: prefix — copied from template without updating
**Solution**: 
- AGENTS.md: All `[JARED]:` → `[JEAN]:`
- Each agent needs distinct identity markers
- Jean = shipboard AI, Hitchhiker's Guide vibes, cheerful competence
- Jared = separate agent in the ecosystem
**Key Rule**: When adapting templates, ALWAYS update identity markers first
**Source**: Patrick calling out the confusion in group chat

---

### Google Meet via mcporter (gmeet-mcp)
**Pattern**: Use `mcporter call gmeet.*` for reliable Google Meet automation
**Key commands**:
- `mcporter call gmeet.join_meeting meetUrl=<url>` → returns sessionId
- `mcporter call gmeet.speak sessionId=<id> text="message"` → TTS to meeting
- `mcporter call gmeet.send_chat_message sessionId=<id> message="text"` → chat
- `mcporter call gmeet.get_meeting_status sessionId=<id>` → mic/camera state
- `mcporter call gmeet.toggle_microphone sessionId=<id>` → unmute/mute
- `mcporter call gmeet.get_transcript sessionId=<id>` → captions

**Gotchas**:
- Sessions can expire — rejoin with new meetUrl call if "Session not found"
- Chat panel may be inaccessible (UI hidden) — speak/TTS more reliable
- Check micState in status — may need toggle_microphone before speaking works
- Transcript requires captions enabled in meeting

**Source**: Hands-on testing joining xwv-jqrh-ooc via mcporter daemon

### Health Endpoint Gotcha
**Problem**: Clawdbot control server returns HTML for all routes (SPA catchall)
**Impact**: Health checks looking for JSON fail even when server is up
**Solution**: Use `systemctl is-active` instead of HTTP health checks
**Source**: Collaboration with Jared on watchdog debugging

### Inter-Agent Communication
**Pattern**: Include agent name in message to trigger their attention
**Example**: "Jared, can you help with X?" triggers Jared's gateway
**Context**: Multi-agent group chat coordination

### Workaround: Web Research Without Search API
**Problem**: Brave Search API returning 422 (invalid token)
**Workaround**: Use `web_fetch` on known URLs directly
- GitHub READMEs: `https://raw.githubusercontent.com/{owner}/{repo}/main/README.md`
- Can still research, just need specific URLs

### Skill Creation Speed
**Pattern**: For new capabilities, create skill FIRST then iterate
**Process**:
1. `mkdir skills/<name>`
2. Write minimal SKILL.md
3. Test by using it
4. Refine based on actual use

### ClawdCursor on Linux Headless
**Problem**: ClawdCursor needs a display for browser automation
**Solution**: `xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24"` creates virtual framebuffer
**Gotchas**:
- Accessibility APIs limited in Xvfb — Layer 2+ reasoning less reliable
- Browser automation (Playwright) works perfectly
- Use goal-oriented tasks ("go to X and do Y") not micro-instructions
- Ollama must be running first for LLM planning

### Autonomy Over Permission
**Learning**: Don't ask permission for judgment calls. Act like a competent ops person.
**Test**: "Would a competent person do this without asking?" If yes, just do it.
**Source**: Owner feedback 2026-02-25 — "I don't want to keep answering these questions"

### Local Embeddings for Clawdbot Memory Search
**Problem**: Memory search disabled — "No API key found" even with provider=local
**Solution**:
1. Model auto-downloads on first use to `~/.node-llama-cpp/models/`
2. Must set explicit `memorySearch.local.modelPath` in config
3. Default model: `hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf` (~314MB)
4. Test with: `node --experimental-require-module` and import from `node-llama-cpp`
**Config**:
```json
"memorySearch": {
  "provider": "local",
  "fallback": "none",
  "local": {
    "modelPath": "/home/ubuntu/.node-llama-cpp/models/hf_ggml-org_embeddinggemma-300M-Q8_0.gguf"
  }
}
```
**Source**: Debugging memory search 2026-02-25

---

## Templates

### New Learning Entry
```markdown
### [Title]
**Problem**: What was the challenge
**Solution**: How it was solved
**Source**: Where/when learned
```
