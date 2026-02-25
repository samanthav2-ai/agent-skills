---
name: whatsapp-media
description: Process images and audio from WhatsApp messages. Use when you receive media attachments (images, voice notes, audio files) in WhatsApp and need to analyze, transcribe, or process them. Handles media download, image analysis via vision models, and audio transcription via Whisper.
---

# WhatsApp Media Processing

## Quick Reference

### Image Processing

```bash
# 1. Find the image file (most recent)
ls -lt ~/.clawdbot/media/inbound/*.jpg ~/.clawdbot/media/inbound/*.png 2>/dev/null | head -5

# 2. Analyze with vision model
image tool: pass the file path to analyze
```

### Audio Transcription

```bash
# 1. Find the audio file (most recent)
ls -lt ~/.clawdbot/media/inbound/*.ogg ~/.clawdbot/media/inbound/*.mp3 2>/dev/null | head -5

# 2. Transcribe with Groq Whisper
curl -s -X POST "https://api.groq.com/openai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/audio.ogg" \
  -F "model=whisper-large-v3" \
  -F "response_format=json" | jq -r '.text'
```

## Media Locations

| Type | Location | Extensions |
|------|----------|------------|
| Images | `~/.clawdbot/media/inbound/` | `.jpg`, `.png`, `.webp` |
| Audio | `~/.clawdbot/media/inbound/` | `.ogg`, `.opus`, `.mp3`, `.m4a` |
| Video | `~/.clawdbot/media/inbound/` | `.mp4` |
| Documents | `~/.clawdbot/media/inbound/` | `.pdf`, `.doc`, etc. |

## Image Analysis

### Using the Image Tool

The `image` tool analyzes images with a vision model:

```
image(image="/path/to/image.jpg", prompt="Describe this image")
```

**When to use:**
- Image was NOT already in the user's message context
- Need detailed analysis of specific aspects
- Processing downloaded/saved images

### Finding Recent Images

```bash
# Most recent image from WhatsApp
find ~/.clawdbot/media/inbound -name "*.jpg" -o -name "*.png" -mmin -5 | head -1
```

## Audio Transcription

### Groq Whisper API

Fastest option for transcription:

```bash
# Load API key
source ~/.clawdbot/.env

# Transcribe
curl -s -X POST "https://api.groq.com/openai/v1/audio/transcriptions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F "file=@$AUDIO_FILE" \
  -F "model=whisper-large-v3" \
  -F "response_format=json" | jq -r '.text'
```

### Supported Formats

Whisper accepts: `.ogg`, `.opus`, `.mp3`, `.m4a`, `.wav`, `.webm`

WhatsApp voice notes are typically `.ogg` (Opus codec).

## Helper Script

See `scripts/process-media.sh` for automated processing:

```bash
./scripts/process-media.sh image /path/to/image.jpg
./scripts/process-media.sh audio /path/to/audio.ogg
```

## Known Limitations

### Current Issues

1. **Store locking**: wacli media download can fail if store is locked by sync daemon
2. **Media placeholders**: Images in messages show as `<media:image>` - need to find actual file
3. **Timing**: Media files appear in inbound dir after message arrives (slight delay)

### Workarounds

- **Images**: Find by timestamp in `~/.clawdbot/media/inbound/`
- **Audio**: Same approach - find most recent `.ogg` file
- **Alternative**: Ask user to share via URL (imgur, paste.pics, etc.)

## Future Improvements

1. **Direct media access**: Hook into Clawdbot media pipeline for direct file access
2. **Media message correlation**: Map message IDs to downloaded file paths
3. **Streaming transcription**: Real-time audio processing for long recordings
4. **Local Whisper**: Run whisper locally for privacy-sensitive audio
5. **Video processing**: Extract frames, transcribe audio track

## Environment Setup

Required in `~/.clawdbot/.env`:

```
GROQ_API_KEY=gsk_...
```

Optional for alternative providers:
```
OPENAI_API_KEY=sk-...
```
