#!/usr/bin/env python3
"""
OS-1 Agent File Transfer Library

Scalable S3-based file transfer between agents with metadata tracking.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, BinaryIO
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 not installed. Run: pip install boto3")
    exit(1)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    exit(1)


class AgentTransfer:
    """File transfer manager for OS-1 agents"""
    
    def __init__(
        self,
        sender: str,
        bucket: str = 'os1-agent-transfers',
        db_connection: Optional[str] = None,
        aws_profile: Optional[str] = None,
        aws_region: str = 'us-east-1'
    ):
        """
        Initialize transfer manager
        
        Args:
            sender: Agent name (samantha, jared, jean)
            bucket: S3 bucket name
            db_connection: PostgreSQL connection string
            aws_profile: AWS CLI profile name (or None for IAM role)
            aws_region: AWS region
        """
        self.sender = sender
        self.bucket = bucket
        self.aws_region = aws_region
        
        # Initialize S3 client
        session = boto3.Session(
            profile_name=aws_profile,
            region_name=aws_region
        )
        self.s3 = session.client('s3')
        
        # Initialize database connection
        if db_connection is None:
            # Default: read from environment or auth-layer config
            db_connection = os.getenv('DATABASE_URL')
            if db_connection is None:
                # Try reading from auth-layer config
                try:
                    with open('/home/ubuntu/clawd/auth-layer/.env', 'r') as f:
                        for line in f:
                            if line.startswith('DATABASE_URL='):
                                db_connection = line.split('=', 1)[1].strip()
                                break
                except FileNotFoundError:
                    pass
        
        if db_connection is None:
            raise ValueError("Database connection string required (DATABASE_URL env or db_connection param)")
        
        self.db_connection = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create agent_transfers table if it doesn't exist"""
        schema = """
        CREATE TABLE IF NOT EXISTS agent_transfers (
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
            expires_at TIMESTAMP NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_recipient_status ON agent_transfers(recipient, status);
        CREATE INDEX IF NOT EXISTS idx_sender ON agent_transfers(sender);
        CREATE INDEX IF NOT EXISTS idx_created ON agent_transfers(created_at);
        """
        
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(schema)
                conn.commit()
    
    def send(
        self,
        file_path: str,
        recipient: str,
        metadata: Optional[Dict] = None,
        expires_hours: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Send file to another agent
        
        Args:
            file_path: Path to file to send
            recipient: Recipient agent name
            metadata: Optional metadata dict
            expires_hours: Hours until file expires (default: 168 = 7 days)
            mime_type: MIME type (auto-detected if None)
        
        Returns:
            transfer_id (UUID)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = file_path.name
        file_size = file_path.stat().st_size
        
        # Auto-detect MIME type
        if mime_type is None:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type is None:
                mime_type = 'application/octet-stream'
        
        # Generate transfer ID and S3 key
        transfer_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        s3_key = f"{self.sender}/{recipient}/{timestamp}_{transfer_id}/{filename}"
        
        # Calculate expiration
        if expires_hours is None:
            expires_hours = 168  # 7 days
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Upload to S3
        try:
            self.s3.upload_file(
                str(file_path),
                self.bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'sender': self.sender,
                        'recipient': recipient,
                        'transfer-id': transfer_id
                    }
                }
            )
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {e}")
        
        # Record in database
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_transfers 
                    (id, sender, recipient, filename, file_size_bytes, mime_type, 
                     s3_key, s3_bucket, metadata, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (transfer_id, self.sender, recipient, filename, file_size,
                     mime_type, s3_key, self.bucket, json.dumps(metadata or {}),
                     expires_at)
                )
                conn.commit()
        
        return transfer_id
    
    def send_buffer(
        self,
        buffer: BinaryIO,
        filename: str,
        recipient: str,
        metadata: Optional[Dict] = None,
        expires_hours: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """
        Send file from memory buffer
        
        Args:
            buffer: File-like object (BytesIO, etc.)
            filename: Filename for the transfer
            recipient: Recipient agent name
            metadata: Optional metadata
            expires_hours: Hours until expiration
            mime_type: MIME type
        
        Returns:
            transfer_id
        """
        # Read buffer
        buffer.seek(0)
        data = buffer.read()
        file_size = len(data)
        
        # Auto-detect MIME type
        if mime_type is None:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type is None:
                mime_type = 'application/octet-stream'
        
        # Generate transfer ID and S3 key
        transfer_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
        s3_key = f"{self.sender}/{recipient}/{timestamp}_{transfer_id}/{filename}"
        
        # Calculate expiration
        if expires_hours is None:
            expires_hours = 168
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Upload to S3
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=data,
                ServerSideEncryption='AES256',
                Metadata={
                    'sender': self.sender,
                    'recipient': recipient,
                    'transfer-id': transfer_id
                }
            )
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {e}")
        
        # Record in database
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_transfers 
                    (id, sender, recipient, filename, file_size_bytes, mime_type, 
                     s3_key, s3_bucket, metadata, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (transfer_id, self.sender, recipient, filename, file_size,
                     mime_type, s3_key, self.bucket, json.dumps(metadata or {}),
                     expires_at)
                )
                conn.commit()
        
        return transfer_id
    
    def list_pending(self, recipient: Optional[str] = None) -> List[Dict]:
        """
        List pending file transfers
        
        Args:
            recipient: Filter by recipient (default: self.sender)
        
        Returns:
            List of transfer records
        """
        if recipient is None:
            recipient = self.sender
        
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, sender, recipient, filename, file_size_bytes,
                           mime_type, metadata, created_at, expires_at
                    FROM agent_transfers
                    WHERE recipient = %s AND status = 'pending'
                    AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY created_at DESC
                    """,
                    (recipient,)
                )
                return [dict(row) for row in cur.fetchall()]
    
    def download(
        self,
        transfer_id: str,
        dest_dir: Optional[str] = None
    ) -> str:
        """
        Download a file transfer
        
        Args:
            transfer_id: Transfer UUID
            dest_dir: Destination directory (default: current dir)
        
        Returns:
            Path to downloaded file
        """
        # Get transfer record
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, sender, recipient, filename, s3_key, s3_bucket, status
                    FROM agent_transfers
                    WHERE id = %s
                    """,
                    (transfer_id,)
                )
                record = cur.fetchone()
        
        if record is None:
            raise ValueError(f"Transfer not found: {transfer_id}")
        
        if record['recipient'] != self.sender:
            raise PermissionError(f"Transfer is for {record['recipient']}, not {self.sender}")
        
        # Download from S3
        if dest_dir is None:
            dest_dir = os.getcwd()
        dest_path = Path(dest_dir) / record['filename']
        
        try:
            self.s3.download_file(
                record['s3_bucket'],
                record['s3_key'],
                str(dest_path)
            )
        except ClientError as e:
            raise RuntimeError(f"S3 download failed: {e}")
        
        # Mark as downloaded
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE agent_transfers
                    SET status = 'downloaded', downloaded_at = NOW()
                    WHERE id = %s
                    """,
                    (transfer_id,)
                )
                conn.commit()
        
        return str(dest_path)
    
    def get_status(self, transfer_id: str) -> Dict:
        """Get transfer status"""
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM agent_transfers
                    WHERE id = %s
                    """,
                    (transfer_id,)
                )
                record = cur.fetchone()
        
        if record is None:
            raise ValueError(f"Transfer not found: {transfer_id}")
        
        return dict(record)
    
    def cleanup_expired(self) -> int:
        """Delete expired transfers from S3 and database"""
        count = 0
        
        with psycopg2.connect(self.db_connection) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Find expired transfers
                cur.execute(
                    """
                    SELECT id, s3_bucket, s3_key
                    FROM agent_transfers
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                    AND status != 'expired'
                    """
                )
                expired = cur.fetchall()
                
                # Delete from S3
                for record in expired:
                    try:
                        self.s3.delete_object(
                            Bucket=record['s3_bucket'],
                            Key=record['s3_key']
                        )
                        count += 1
                    except ClientError as e:
                        print(f"Warning: Could not delete {record['s3_key']}: {e}")
                
                # Update status
                if expired:
                    cur.execute(
                        """
                        UPDATE agent_transfers
                        SET status = 'expired'
                        WHERE expires_at IS NOT NULL AND expires_at < NOW()
                        """
                    )
                    conn.commit()
        
        return count


if __name__ == '__main__':
    # Simple CLI usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python os1_transfer.py <command> [args]")
        print("Commands: send, list, download, status, cleanup")
        sys.exit(1)
    
    # Determine sender from environment or default
    sender = os.getenv('AGENT_NAME', 'samantha')
    
    transfer = AgentTransfer(sender=sender)
    
    command = sys.argv[1]
    
    if command == 'send':
        if len(sys.argv) < 4:
            print("Usage: python os1_transfer.py send <file> <recipient>")
            sys.exit(1)
        file_path = sys.argv[2]
        recipient = sys.argv[3]
        transfer_id = transfer.send(file_path, recipient)
        print(f"Sent: {transfer_id}")
    
    elif command == 'list':
        pending = transfer.list_pending()
        if not pending:
            print("No pending transfers")
        else:
            for record in pending:
                print(f"{record['id']}: {record['filename']} from {record['sender']} ({record['file_size_bytes']} bytes)")
    
    elif command == 'download':
        if len(sys.argv) < 3:
            print("Usage: python os1_transfer.py download <transfer-id>")
            sys.exit(1)
        transfer_id = sys.argv[2]
        path = transfer.download(transfer_id)
        print(f"Downloaded: {path}")
    
    elif command == 'status':
        if len(sys.argv) < 3:
            print("Usage: python os1_transfer.py status <transfer-id>")
            sys.exit(1)
        transfer_id = sys.argv[2]
        status = transfer.get_status(transfer_id)
        print(json.dumps(status, default=str, indent=2))
    
    elif command == 'cleanup':
        count = transfer.cleanup_expired()
        print(f"Cleaned up {count} expired transfers")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
