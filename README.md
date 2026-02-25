# Agent Skills

Reusable skills for Clawdbot agents — media processing, integrations, and automation.

## Available Skills

### vector-store

Semantic search and persistent knowledge storage for multi-agent coordination.

**Capabilities:**
- 🗄️ Shared Postgres with pgvector for cross-agent knowledge
- 🔍 Semantic search over learnings and documentation
- 📬 Inter-agent messaging queue
- ✅ Task coordination tables

**Usage:**
```bash
# Store knowledge
./vector-store/scripts/store-knowledge.sh --agent jean --title "My Learning" --content "..."

# Query knowledge
./vector-store/scripts/pg-query.sh "SELECT * FROM agent_knowledge"
```

See [vector-store/SKILL.md](vector-store/SKILL.md) for full documentation.

### inter-agent

Multi-agent coordination protocols for the Brotherhood of Claw.

**Capabilities:**
- 🤝 Task handoffs and status tracking
- 📊 Standup protocol (30-min intervals)
- 🚨 Emergency/SOS protocols
- ⚖️ Dispute resolution
- 📋 Priority levels (P1-P5)

**Usage:**
Follow the message patterns and standup format documented in the skill.

See [inter-agent/SKILL.md](inter-agent/SKILL.md) for full protocols.

### proactive-notify

Surface interesting things without being asked. Reduce cognitive load by flagging what matters.

**Capabilities:**
- 🔔 Pattern-based notification system
- 📊 Priority scoring (high/medium/low)
- ⏱️ Cooldown/debounce to prevent spam
- 📋 GitHub, email, calendar, social scanners

**Usage:**
```bash
# Scan for notifications
python3 proactive-notify/scan.py

# Check for immediate alerts only
python3 proactive-notify/scan.py --alerts
```

See [proactive-notify/SKILL.md](proactive-notify/SKILL.md) for configuration.

### resilient-coding-agent

Run long-running coding agents in tmux sessions that survive orchestrator restarts.

**Capabilities:**
- 🛡️ Process decoupling via tmux
- 🔄 Automatic resume on interruption
- 📋 Support for Codex, Claude Code, OpenCode, Pi

**Usage:**
```bash
# Start a long-running task
tmux new-session -d -s codex-task
tmux send-keys -t codex-task 'codex exec --full-auto "<prompt>"' Enter

# Monitor progress
tmux capture-pane -t codex-task -p -S -200
```

See [resilient-coding-agent/SKILL.md](resilient-coding-agent/SKILL.md) for patterns.

### exchange-rate

Real-time forex and cryptocurrency exchange rate lookup and conversion.

**Capabilities:**
- 💱 Multi-provider fallback (QVeris)
- 🪙 Crypto support (BTC, ETH, etc.)
- 📊 Amount conversion

**Usage:**
```bash
# Get exchange rate
node exchange-rate/scripts/exchange_rate.mjs USD EUR

# Convert amount
node exchange-rate/scripts/exchange_rate.mjs USD EUR 100
```

See [exchange-rate/SKILL.md](exchange-rate/SKILL.md) for details.

### whatsapp-media

Process images and audio from WhatsApp messages.

**Capabilities:**
- 🖼️ Image analysis via vision models
- 🎤 Audio transcription via Groq Whisper
- 📁 Media file discovery in Clawdbot inbound directory

**Usage:**
```bash
# Transcribe audio
./whatsapp-media/scripts/process-media.sh audio /path/to/voice-note.ogg

# Find and transcribe most recent audio
./whatsapp-media/scripts/process-media.sh recent-audio

# List recent images
./whatsapp-media/scripts/process-media.sh list-images
```

See [whatsapp-media/SKILL.md](whatsapp-media/SKILL.md) for full documentation.

## Installation

### For Clawdbot Agents

Copy skills to your workspace:

```bash
cp -r whatsapp-media ~/clawd/skills/
```

Or symlink:

```bash
ln -s $(pwd)/whatsapp-media ~/clawd/skills/whatsapp-media
```

### Environment Setup

Required in `~/.clawdbot/.env`:

```
GROQ_API_KEY=gsk_...  # For audio transcription
```

## Roadmap / Improvements Needed

### Media Processing

- [ ] **Direct media access**: Hook into Clawdbot's media pipeline for direct file access instead of scanning inbound directory
- [ ] **Message-to-file correlation**: Map WhatsApp message IDs to downloaded file paths
- [ ] **Store locking fix**: Handle wacli store lock conflicts with sync daemon
- [ ] **Streaming transcription**: Real-time audio processing for long recordings
- [ ] **Local Whisper**: Option to run whisper locally for privacy-sensitive audio

### Image Processing

- [ ] **OCR extraction**: Dedicated text extraction from images
- [ ] **Document processing**: Handle PDFs and office documents
- [ ] **Image editing**: Basic operations (crop, resize, annotate)

### Audio Processing

- [ ] **Speaker diarization**: Identify different speakers in audio
- [ ] **Translation**: Transcribe + translate in one step
- [ ] **Voice cloning prep**: Extract voice characteristics for TTS

### Video Processing

- [ ] **Frame extraction**: Pull key frames from video
- [ ] **Audio track transcription**: Extract and transcribe video audio
- [ ] **Clip generation**: Create short clips from longer videos

## Contributing

1. Fork this repo
2. Create a skill in a new directory
3. Include a `SKILL.md` with proper frontmatter
4. Add helper scripts in `scripts/` if needed
5. Update this README
6. Submit PR

### Skill Structure

```
skill-name/
├── SKILL.md           # Required: frontmatter + instructions
├── scripts/           # Optional: helper scripts
├── references/        # Optional: documentation
└── assets/            # Optional: templates, etc.
```

## License

MIT
