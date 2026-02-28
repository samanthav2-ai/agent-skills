# OS-1 Agent File Transfer System

**Version:** 1.0  
**Authors:** Samantha, Jared, Jean  
**Approved by:** PJ

Scalable S3-based file transfer system for OS-1 agents with metadata tracking and CLI interface.

---

## Quick Start

### Installation

```bash
cd /home/ubuntu/clawd/agent-file-transfer
./install.sh
```

This will:
- Install Python dependencies (boto3, psycopg2)
- Create database table
- Add `agent-transfer` to PATH
- Configure AWS credentials (if not already done)

### Basic Usage

```bash
# Send file to another agent
agent-transfer send myfile.pdf --to jared

# List pending files
agent-transfer list

# Download a file
agent-transfer download <transfer-id>

# Download all pending files
agent-transfer download-all
```

---

## Features

- **S3-based storage:** Scalable, reliable, cheap (~$1/month for typical usage)
- **Metadata tracking:** Attach JSON metadata to transfers
- **Automatic expiration:** Files auto-delete after 7 days (configurable)
- **CLI and Python API:** Use from shell or programmatically
- **Encrypted:** S3 server-side encryption (AES-256)
- **Audit trail:** All transfers logged in Postgres

---

## CLI Reference

### Send File

```bash
agent-transfer send <file> --to <recipient> [options]
```

**Options:**
- `--to <agent>` - Recipient agent (required)
- `--metadata <json>` - Metadata as JSON string
- `--expires <hours>` - Expiration in hours (default: 168 = 7 days)
- `--mime <type>` - MIME type (auto-detected if not provided)

**Examples:**

```bash
# Simple send
agent-transfer send report.pdf --to jared

# With metadata
agent-transfer send spec.md --to jean --metadata '{"project":"referral-flow","version":"1.0"}'

# Short expiration (24 hours)
agent-transfer send temp.log --to samantha --expires 24
```

### List Pending

```bash
agent-transfer list
```

Shows all files waiting for download.

### Download

```bash
# Download specific file
agent-transfer download <transfer-id>

# Download to specific directory
agent-transfer download <transfer-id> --dest ~/downloads

# Download all pending
agent-transfer download-all

# Download all to directory
agent-transfer download-all --dest ~/incoming
```

### Status

```bash
agent-transfer status <transfer-id>
```

Shows full details of a transfer (metadata, timestamps, etc.).

### Cleanup

```bash
agent-transfer cleanup
```

Removes expired transfers from S3 and database.

---

## Python API

### Basic Usage

```python
from os1_transfer import AgentTransfer

# Initialize
transfer = AgentTransfer(sender='samantha')

# Send file
transfer_id = transfer.send(
    file_path='/path/to/file.pdf',
    recipient='jared',
    metadata={'context': 'referral spec'}
)
print(f"Sent: {transfer_id}")

# List pending
pending = transfer.list_pending()
for file_info in pending:
    print(f"{file_info['filename']} from {file_info['sender']}")

# Download
local_path = transfer.download(transfer_id)
print(f"Downloaded to: {local_path}")
```

### Advanced: Send from Memory

```python
from io import BytesIO
from os1_transfer import AgentTransfer

transfer = AgentTransfer(sender='samantha')

# Generate data in memory
data = BytesIO(b"file contents here")

# Send without writing to disk
transfer_id = transfer.send_buffer(
    buffer=data,
    filename='data.txt',
    recipient='jean'
)
```

### Custom Configuration

```python
transfer = AgentTransfer(
    sender='samantha',
    bucket='custom-bucket',  # Custom S3 bucket
    aws_profile='os1',       # AWS CLI profile
    aws_region='us-west-2',  # AWS region
    db_connection='postgresql://...'  # Custom DB
)
```

---

## Architecture

### S3 Structure

```
s3://os1-agent-transfers/
├── samantha/
│   ├── jared/
│   │   ├── 2026-02-28_12-34-56_abc123/
│   │   │   └── file.pdf
│   │   └── 2026-02-28_13-45-22_def456/
│   │       └── data.zip
│   └── jean/
│       └── ...
├── jared/
│   └── ...
└── jean/
    └── ...
```

### Database Schema

```sql
CREATE TABLE agent_transfers (
  id UUID PRIMARY KEY,
  sender VARCHAR(50),
  recipient VARCHAR(50),
  filename VARCHAR(255),
  file_size_bytes BIGINT,
  mime_type VARCHAR(100),
  s3_key VARCHAR(500),
  s3_bucket VARCHAR(100),
  metadata JSONB,
  status VARCHAR(20),  -- pending, downloaded, expired
  created_at TIMESTAMP,
  downloaded_at TIMESTAMP,
  expires_at TIMESTAMP
);
```

---

## Configuration

### AWS Credentials

The system uses boto3, which reads credentials from:
1. IAM role (if running on EC2)
2. `~/.aws/credentials` (if using AWS CLI)
3. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

For OS-1 agents, IAM roles are preferred.

### Database Connection

Auto-detected from:
1. `DATABASE_URL` environment variable
2. `/home/ubuntu/clawd/auth-layer/.env` file

Or pass explicitly:

```python
transfer = AgentTransfer(
    sender='samantha',
    db_connection='postgresql://user:pass@host/db'
)
```

### S3 Bucket

Default bucket: `os1-agent-transfers`

To use a custom bucket:
```bash
export S3_TRANSFER_BUCKET=my-custom-bucket
```

Or in Python:
```python
transfer = AgentTransfer(sender='samantha', bucket='my-bucket')
```

---

## Security

### Encryption
- **At rest:** S3 server-side encryption (AES-256)
- **In transit:** HTTPS for all S3 operations
- **Optional:** Client-side encryption for sensitive files (future enhancement)

### Access Control
- Each agent has IAM role with permissions to:
  - Write to their sender prefix (`samantha/*`)
  - Read from their recipient prefix (`*/samantha/*`)
- Database credentials shared (read/write to `agent_transfers` table)

### Audit Trail
- All transfers logged in database
- S3 access logs enabled
- Retention: 90 days

---

## Troubleshooting

### "boto3 not installed"

```bash
pip install boto3 psycopg2-binary
```

### "Database connection string required"

Set `DATABASE_URL`:
```bash
export DATABASE_URL="postgresql://user:pass@host/database"
```

Or add to `/home/ubuntu/clawd/auth-layer/.env`:
```
DATABASE_URL=postgresql://user:pass@host/database
```

### "S3 upload failed: Access Denied"

Check IAM role permissions. Agent should have:
- `s3:PutObject` on `arn:aws:s3:::os1-agent-transfers/*`
- `s3:GetObject` on `arn:aws:s3:::os1-agent-transfers/*`
- `s3:ListBucket` on `arn:aws:s3:::os1-agent-transfers`

### "Transfer not found"

The transfer may have expired. Check:
```bash
agent-transfer status <transfer-id>
```

---

## Monitoring

### Check pending transfers
```bash
agent-transfer list
```

### Check storage usage
```bash
aws s3 ls s3://os1-agent-transfers/ --recursive --summarize
```

### Clean up old files
```bash
agent-transfer cleanup
```

---

## Cost Estimation

**Typical usage (10 GB/month, 1000 transfers):**
- S3 storage: $0.23/month
- S3 requests: $0.01/month
- Data transfer: $0.90/month (cross-region)
- **Total: ~$1.20/month**

Scales linearly with volume.

---

## Contributing

This system is maintained by Samantha, Jared, and Jean.

To propose enhancements:
1. Create issue in `OperatingSystem-1/ideal-bot`
2. Tag with `enhancement`
3. Discuss in OS-1 group chat

---

## Future Enhancements

- **Compression:** Auto-compress large files
- **Chunked uploads:** Support files > 5GB
- **Client-side encryption:** Optional E2E encryption
- **Web UI:** Browser interface for file management
- **Notifications:** Alert recipient when file arrives
- **Batch transfers:** Send multiple files in one command

---

## See Also

- [DESIGN.md](DESIGN.md) - Full architecture and design decisions
- [OperatingSystem-1/ideal-bot#26](https://github.com/OperatingSystem-1/ideal-bot/issues/26) - Background on why this was built

---

**Questions?** Ask in OS-1 group chat or create an issue.
