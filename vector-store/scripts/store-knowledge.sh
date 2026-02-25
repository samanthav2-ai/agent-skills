#!/bin/bash
# Store knowledge in shared Postgres
# Usage: ./store-knowledge.sh --agent jean --category debugging --title "My Title" --content "Content here"

PGCONNECTION="${VECTOR_STORE_PG:-postgresql://neondb_owner:npg_24bYhdRcyZax@ep-polished-bread-ai1pqzi9-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent) AGENT="$2"; shift 2 ;;
        --category) CATEGORY="$2"; shift 2 ;;
        --title) TITLE="$2"; shift 2 ;;
        --content) CONTENT="$2"; shift 2 ;;
        --tags) TAGS="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [ -z "$AGENT" ] || [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
    echo "Usage: $0 --agent <name> --title <title> --content <content> [--category <cat>] [--tags <tags>]"
    exit 1
fi

CATEGORY="${CATEGORY:-general}"
METADATA="{\"tags\": [\"${TAGS:-untagged}\"], \"added\": \"$(date -Iseconds)\"}"

psql "$PGCONNECTION" -c "
INSERT INTO agent_knowledge (agent_name, category, title, content, metadata)
VALUES ('$AGENT', '$CATEGORY', '$TITLE', '$CONTENT', '$METADATA');
"

echo "✅ Knowledge stored: $TITLE"
