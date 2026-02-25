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
