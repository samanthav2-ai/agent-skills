#!/bin/bash
# Quick Postgres query helper for vector store
# Usage: ./pg-query.sh "SELECT * FROM agent_knowledge"

PGCONNECTION="${VECTOR_STORE_PG:-postgresql://neondb_owner:npg_24bYhdRcyZax@ep-polished-bread-ai1pqzi9-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require}"

if [ -z "$1" ]; then
    echo "Usage: $0 <sql-query>"
    echo ""
    echo "Examples:"
    echo "  $0 \"SELECT * FROM agent_knowledge\""
    echo "  $0 \"SELECT * FROM agent_tasks WHERE status = 'open'\""
    exit 1
fi

psql "$PGCONNECTION" -c "$1"
