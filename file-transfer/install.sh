#!/usr/bin/env bash
#
# install.sh - Install OS-1 Agent File Transfer System
#

set -euo pipefail

echo "🚀 Installing OS-1 Agent File Transfer System..."
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --quiet boto3 psycopg2-binary

echo "✓ Dependencies installed"

# Create symlink to make agent-transfer available system-wide
INSTALL_DIR="/usr/local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -w "$INSTALL_DIR" ]]; then
    ln -sf "$SCRIPT_DIR/agent-transfer" "$INSTALL_DIR/agent-transfer"
    echo "✓ agent-transfer → $INSTALL_DIR/agent-transfer"
else
    echo "⚠️  Cannot write to $INSTALL_DIR, skipping symlink"
    echo "   Add to PATH manually: export PATH=\"$SCRIPT_DIR:\$PATH\""
fi

# Determine agent name
if [[ -z "${AGENT_NAME:-}" ]]; then
    # Try to infer from hostname
    AGENT_NAME=$(hostname | grep -oE '(samantha|jared|jean)' || echo "")
    
    if [[ -z "$AGENT_NAME" ]]; then
        echo
        echo "⚠️  Could not determine agent name from hostname"
        echo "   Set manually: export AGENT_NAME=samantha"
        AGENT_NAME="samantha"
    fi
fi

echo "✓ Agent: $AGENT_NAME"

# Check database connection
echo
echo "🗄️  Checking database connection..."

DB_URL=""
if [[ -n "${DATABASE_URL:-}" ]]; then
    DB_URL="$DATABASE_URL"
elif [[ -f "/home/ubuntu/clawd/auth-layer/.env" ]]; then
    DB_URL=$(grep '^DATABASE_URL=' /home/ubuntu/clawd/auth-layer/.env | cut -d= -f2- || echo "")
fi

if [[ -z "$DB_URL" ]]; then
    echo "⚠️  DATABASE_URL not found"
    echo "   Set it in /home/ubuntu/clawd/auth-layer/.env or export DATABASE_URL=..."
    echo "   Format: postgresql://user:pass@host/database"
else
    echo "✓ Database configured"
    
    # Create table
    echo "📊 Creating agent_transfers table..."
    python3 -c "from os1_transfer import AgentTransfer; AgentTransfer('$AGENT_NAME')._ensure_table_exists()" 2>/dev/null || echo "⚠️  Could not create table (may already exist)"
fi

# Check AWS credentials
echo
echo "☁️  Checking AWS credentials..."

if aws sts get-caller-identity &>/dev/null; then
    echo "✓ AWS credentials configured"
    IDENTITY=$(aws sts get-caller-identity --query 'Arn' --output text)
    echo "  Identity: $IDENTITY"
else
    echo "⚠️  AWS credentials not configured"
    echo "   Option 1: Use IAM role (recommended for EC2)"
    echo "   Option 2: Configure AWS CLI: aws configure"
    echo "   Option 3: Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
fi

# Check S3 bucket
echo
echo "📦 Checking S3 bucket..."
BUCKET="os1-agent-transfers"

if aws s3 ls "s3://$BUCKET" &>/dev/null; then
    echo "✓ Bucket s3://$BUCKET exists"
else
    echo "⚠️  Bucket s3://$BUCKET not found"
    echo "   Create it: aws s3 mb s3://$BUCKET"
    echo "   Or use a custom bucket: export S3_TRANSFER_BUCKET=my-bucket"
fi

# Test installation
echo
echo "🧪 Testing installation..."

if command -v agent-transfer &>/dev/null; then
    echo "✓ agent-transfer command available"
    
    # Try listing (should work even if no transfers)
    if agent-transfer list &>/dev/null; then
        echo "✓ Database connection works"
    else
        echo "⚠️  Database connection failed (check DATABASE_URL)"
    fi
else
    echo "⚠️  agent-transfer not in PATH"
    echo "   Add: export PATH=\"$SCRIPT_DIR:\$PATH\""
fi

echo
echo "✅ Installation complete!"
echo
echo "Quick start:"
echo "  agent-transfer send myfile.pdf --to jared"
echo "  agent-transfer list"
echo "  agent-transfer download <transfer-id>"
echo
echo "Full documentation: $SCRIPT_DIR/README.md"
