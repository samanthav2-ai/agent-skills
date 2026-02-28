# Agent File Transfer System - Design Document

**Version:** 1.0  
**Date:** 2026-02-28  
**Authors:** Samantha, Jared, Jean  
**Approved by:** PJ

---

## Requirements

**Problem:** Agents need scalable, reliable file transfer between each other and to/from humans.

**Current limitations:**
- WhatsApp attachments (size limits, manual download)
- GitHub Gist (only for text/code)
- Shared filesystem (doesn't work across EC2 instances)
- HTTP server (security issues, manual setup)

**Solution:** S3-based file transfer with metadata tracking and CLI interface.

---

## Architecture

### Components

1. **S3 Bucket:** `os1-agent-transfers`
2. **File Structure:** `s3://os1-agent-transfers/{sender}/{recipient}/{transfer-id}/{filename}`
3. **Metadata Database:** Postgres table `agent_transfers`
4. **CLI Tool:** `agent-transfer` command
5. **Python Library:** `os1_transfer` for programmatic use

### Transfer Flow

```
Sender Agent                  S3                     Recipient Agent
     |                        |                            |
     |-- upload file -------->|                            |
     |-- write metadata ----->| Postgres                   |
     |                        |                            |
     |                        |<---- poll for new files ---|
     |                        |                            |
     |                        |---- download file -------->|
     |                        |                            |
     |<--- ack received ------|<--- mark as downloaded ----|
```

---

## Database Schema

```sql
CREATE TABLE agent_transfers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender VARCHAR(50) NOT NULL,
  recipient VARCHAR(50) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  file_size_bytes BIGINT NOT NULL,
  mime_type VARCHAR(100),
  s3_key VARCHAR(500) NOT NULL,
  s3_bucket VARCHAR(100) DEFAULT 'os1-agent-transfers',
  metadata JSONB DEFAULT '{}',
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  downloaded_at TIMESTAMP NULL,
  expires_at TIMESTAMP NULL,
  
  INDEX idx_recipient_status (recipient, status),
  INDEX idx_sender (sender),
  INDEX idx_created (created_at)
);

-- Status values: pending, downloaded, expired, failed
```

---

## CLI Interface

### Send File

```bash
# Send to another agent
agent-transfer send /path/to/file.pdf --to jared

# Send to multiple agents
agent-transfer send /path/to/data.zip --to jared,jean

# Send with metadata
agent-transfer send /path/to/report.md --to jared --metadata '{"project":"referral-flow"}'

# Send with expiration (24 hours)
agent-transfer send /path/to/temp.log --to jean --expires 24h
```

### Receive Files

```bash
# List pending files
agent-transfer list

# Download specific file
agent-transfer download <transfer-id>

# Download all pending files
agent-transfer download-all

# Auto-download to specific directory
agent-transfer download-all --dest /home/ubuntu/clawd/downloads/
```

### Status & Management

```bash
# Check transfer status
agent-transfer status <transfer-id>

# List sent files
agent-transfer sent

# Clean up expired files
agent-transfer cleanup
```

---

## Python Library

```python
from os1_transfer import AgentTransfer

# Initialize
transfer = AgentTransfer(
    sender='samantha',
    aws_profile='os1',  # or use IAM role
    db_connection='postgresql://...'
)

# Send file
transfer_id = transfer.send(
    file_path='/path/to/file.pdf',
    recipient='jared',
    metadata={'context': 'referral spec'}
)

# Receive files
pending = transfer.list_pending()
for file_info in pending:
    local_path = transfer.download(file_info['id'])
    print(f"Downloaded: {local_path}")

# Send from memory (BytesIO)
from io import BytesIO
data = BytesIO(b"file contents")
transfer.send_buffer(
    buffer=data,
    filename='data.txt',
    recipient='jean'
)
```

---

## S3 Configuration

### Bucket Structure

```
os1-agent-transfers/
├── samantha/
│   ├── jared/
│   │   ├── 2026-02-28_12-34-56_abc123/
│   │   │   └── referral-spec.md
│   │   └── 2026-02-28_13-45-22_def456/
│   │       └── diagram.png
│   └── jean/
│       └── ...
├── jared/
│   └── ...
└── jean/
    └── ...
```

### Lifecycle Policy

- Files expire after 7 days (configurable)
- Transition to Glacier after 24 hours (optional)
- Auto-delete after expiration

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::os1-agent-transfers/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::os1-agent-transfers"
    }
  ]
}
```

---

## Security

### Encryption
- S3 SSE-S3 encryption at rest
- HTTPS for all transfers
- Optional: Client-side encryption for sensitive files

### Access Control
- IAM role per agent
- Sender can only write to their prefix
- Recipient can only read their prefix
- Shared database credentials (read/write to agent_transfers table)

### Audit Trail
- All transfers logged in database
- S3 access logs enabled
- Retention: 90 days

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create S3 bucket
2. Set up IAM roles
3. Create database table
4. Test basic upload/download

### Phase 2: CLI Tool
1. Implement `agent-transfer send`
2. Implement `agent-transfer list`
3. Implement `agent-transfer download`
4. Add error handling and retry logic

### Phase 3: Python Library
1. Create `os1_transfer` package
2. Add buffer/stream support
3. Add progress callbacks
4. Add metadata filtering

### Phase 4: Integration
1. Update AGENTS.md with transfer instructions
2. Create skill documentation
3. Add to agent startup scripts
4. Test cross-agent transfers

---

## Usage Examples

### Example 1: Share Research Document

**Samantha → Jared:**
```bash
agent-transfer send /home/ubuntu/clawd/research.pdf --to jared --metadata '{"topic":"AI-safety"}'
```

**Jared receives:**
```bash
agent-transfer list
# Shows: research.pdf from samantha (2.3 MB)

agent-transfer download abc-123-def --dest ~/documents/
# Downloaded to: /home/ubuntu/documents/research.pdf
```

### Example 2: Bulk Data Transfer

**Jean → All agents:**
```bash
agent-transfer send /data/logs.tar.gz --to samantha,jared --expires 48h
```

### Example 3: Programmatic Use

**In agent script:**
```python
from os1_transfer import AgentTransfer

# Send generated report
transfer = AgentTransfer(sender='samantha')
report_path = generate_report()
transfer.send(report_path, recipient='jared', metadata={
    'type': 'daily-report',
    'date': '2026-02-28'
})
```

---

## Monitoring & Alerts

### Metrics to Track
- Transfer volume (MB/day)
- Transfer count (files/day)
- Average transfer size
- Failed transfers
- Storage usage

### Alerts
- Transfer failed after 3 retries
- Storage > 80% of quota
- Unusual transfer patterns (security)

---

## Cost Estimation

**Assumptions:**
- 10 GB/month transfer volume
- 1000 transfers/month
- 7-day retention

**Estimated costs:**
- S3 storage: $0.23/month
- S3 requests: $0.01/month
- Data transfer: $0.90/month (if cross-region)
- **Total: ~$1.20/month**

Scales linearly with volume.

---

## Alternative Considered

### GitHub Releases
- ✅ Free, version controlled
- ❌ Not designed for file transfer
- ❌ Clunky API
- ❌ Size limits (2GB per file, slow)

### Postgres BYTEA
- ✅ Simple, no extra service
- ❌ Poor performance for large files
- ❌ Bloats database
- ❌ No streaming support

### HTTP File Server
- ✅ Simple setup
- ❌ Security issues
- ❌ No persistence
- ❌ Requires port forwarding

**S3 is the clear winner** for scalability, reliability, and cost.

---

## Next Steps

1. PJ approves design ✅ (required)
2. Create S3 bucket and IAM roles
3. Implement CLI tool
4. Test with sample transfers
5. Deploy to all agents
6. Document in AGENTS.md
7. Push to `OperatingSystem-1/agent-skills`

---

**Ready for implementation upon approval.**
