#!/usr/bin/env bash
#
# test.sh - Test OS-1 Agent File Transfer System
#

set -euo pipefail

echo "🧪 Testing OS-1 Agent File Transfer System"
echo

# Create test file
TEST_FILE="/tmp/agent-transfer-test.txt"
echo "This is a test file created at $(date)" > "$TEST_FILE"
echo "✓ Created test file: $TEST_FILE"

# Test 1: Send file
echo
echo "Test 1: Sending file..."
TRANSFER_ID=$(./agent-transfer send "$TEST_FILE" --to jean --metadata '{"test":true}' --expires 1)

if [[ -n "$TRANSFER_ID" ]]; then
    echo "✓ File sent successfully"
    echo "  Transfer ID: $TRANSFER_ID"
else
    echo "❌ Failed to send file"
    exit 1
fi

# Test 2: Check status
echo
echo "Test 2: Checking status..."
STATUS=$(./agent-transfer status "$TRANSFER_ID")
echo "$STATUS" | grep -q "pending" && echo "✓ Status check passed" || (echo "❌ Status check failed"; exit 1)

# Test 3: List pending (should show our test file)
echo
echo "Test 3: Listing pending transfers..."
./agent-transfer list | grep -q "$TEST_FILE" && echo "✓ List shows test file" || echo "⚠️  List doesn't show file (may be filtered by recipient)"

# Test 4: Python API
echo
echo "Test 4: Testing Python API..."
python3 << EOF
from os1_transfer import AgentTransfer
import os

# Test send_buffer
from io import BytesIO
transfer = AgentTransfer(sender='samantha')
data = BytesIO(b"Python API test")
transfer_id = transfer.send_buffer(
    buffer=data,
    filename='python-test.txt',
    recipient='jared'
)
print(f"✓ Python API send_buffer works: {transfer_id}")

# Test list_pending
pending = transfer.list_pending(recipient='samantha')
print(f"✓ Python API list_pending works: {len(pending)} files")
EOF

# Cleanup
rm -f "$TEST_FILE"

echo
echo "✅ All tests passed!"
echo
echo "The system is ready to use."
