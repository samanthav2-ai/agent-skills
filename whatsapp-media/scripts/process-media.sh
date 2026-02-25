#!/bin/bash
# WhatsApp Media Processing Script
# Usage: ./process-media.sh <type> <file>
#   type: image | audio | recent-image | recent-audio
#   file: path to media file (optional for recent-* types)

set -euo pipefail

MEDIA_DIR="${CLAWDBOT_MEDIA_DIR:-$HOME/.clawdbot/media/inbound}"

# Load environment
if [[ -f "$HOME/.clawdbot/.env" ]]; then
    source "$HOME/.clawdbot/.env"
fi

usage() {
    echo "Usage: $0 <command> [file]"
    echo ""
    echo "Commands:"
    echo "  image <file>       Analyze an image (outputs description)"
    echo "  audio <file>       Transcribe audio file"
    echo "  recent-image       Find and analyze most recent image"
    echo "  recent-audio       Find and transcribe most recent audio"
    echo "  list-images        List recent images"
    echo "  list-audio         List recent audio files"
    exit 1
}

find_recent_image() {
    find "$MEDIA_DIR" \( -name "*.jpg" -o -name "*.png" -o -name "*.webp" \) \
        -type f -mmin -60 -printf '%T@ %p\n' 2>/dev/null | \
        sort -rn | head -1 | cut -d' ' -f2-
}

find_recent_audio() {
    find "$MEDIA_DIR" \( -name "*.ogg" -o -name "*.opus" -o -name "*.mp3" -o -name "*.m4a" \) \
        -type f -mmin -60 -printf '%T@ %p\n' 2>/dev/null | \
        sort -rn | head -1 | cut -d' ' -f2-
}

transcribe_audio() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        echo "Error: File not found: $file" >&2
        exit 1
    fi
    
    if [[ -z "${GROQ_API_KEY:-}" ]]; then
        echo "Error: GROQ_API_KEY not set" >&2
        exit 1
    fi
    
    curl -s -X POST "https://api.groq.com/openai/v1/audio/transcriptions" \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@$file" \
        -F "model=whisper-large-v3" \
        -F "response_format=json" | jq -r '.text'
}

analyze_image() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        echo "Error: File not found: $file" >&2
        exit 1
    fi
    
    # Output file path for use with Clawdbot image tool
    echo "IMAGE_PATH=$file"
    echo ""
    echo "To analyze, use the image tool with this path."
    echo "Or view at: file://$file"
}

list_images() {
    echo "Recent images (last 60 min):"
    find "$MEDIA_DIR" \( -name "*.jpg" -o -name "*.png" -o -name "*.webp" \) \
        -type f -mmin -60 -printf '%T+ %p\n' 2>/dev/null | sort -r | head -10
}

list_audio() {
    echo "Recent audio (last 60 min):"
    find "$MEDIA_DIR" \( -name "*.ogg" -o -name "*.opus" -o -name "*.mp3" -o -name "*.m4a" \) \
        -type f -mmin -60 -printf '%T+ %p\n' 2>/dev/null | sort -r | head -10
}

# Main
[[ $# -lt 1 ]] && usage

command="$1"
file="${2:-}"

case "$command" in
    image)
        [[ -z "$file" ]] && { echo "Error: file required"; usage; }
        analyze_image "$file"
        ;;
    audio)
        [[ -z "$file" ]] && { echo "Error: file required"; usage; }
        transcribe_audio "$file"
        ;;
    recent-image)
        file=$(find_recent_image)
        [[ -z "$file" ]] && { echo "No recent images found"; exit 1; }
        echo "Found: $file"
        analyze_image "$file"
        ;;
    recent-audio)
        file=$(find_recent_audio)
        [[ -z "$file" ]] && { echo "No recent audio found"; exit 1; }
        echo "Found: $file"
        transcribe_audio "$file"
        ;;
    list-images)
        list_images
        ;;
    list-audio)
        list_audio
        ;;
    *)
        usage
        ;;
esac
