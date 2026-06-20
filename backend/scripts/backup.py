#!/usr/bin/env python3
"""
Backup automatizado do PostgreSQL (Railway Cron job ou agendador).

Uso:
    python scripts/backup.py

Requer env vars:
    DATABASE_URL — conexão PostgreSQL
    ENCRYPTION_KEY — chave AES-256 para criptografar o dump
    BACKUP_DIR — diretório de destino (default: /data/backups)
"""
import os
import sys
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def parse_db_url(url: str) -> dict:
    """Extrai host, port, user, password, dbname de DATABASE_URL."""
    # postgresql://user:pass@host:port/dbname
    no_scheme = url.replace("postgresql://", "").replace("postgres://", "")
    if "+asyncpg" in no_scheme:
        no_scheme = no_scheme.replace("+asyncpg", "")
    # Also handle postgresql+psycopg2://
    if "+" in no_scheme.split("@")[0]:
        no_scheme = no_scheme.split("+")[0] + no_scheme[no_scheme.index("@") :]

    user_pass, rest = no_scheme.split("@", 1)
    user, password = user_pass.split(":", 1) if ":" in user_pass else (user_pass, "")
    host_port, dbname = rest.split("/", 1) if "/" in rest else (rest, "postgres")
    host, port = host_port.split(":", 1) if ":" in host_port else (host_port, "5432")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }


def encrypt_backup(filepath: Path) -> str:
    """Criptografa arquivo de backup com AES-256 (via openssl)."""
    key = os.getenv("ENCRYPTION_KEY", os.getenv("SECRET_KEY", ""))
    if not key:
        print("WARNING: No ENCRYPTION_KEY set. Skipping encryption.")
        return ""

    key_hex = hashlib.sha256(key.encode()).hexdigest()
    enc_path = str(filepath) + ".enc"

    subprocess.run([
        "openssl", "enc", "-aes-256-cbc",
        "-salt",
        "-in", str(filepath),
        "-out", enc_path,
        "-pass", f"pass:{key_hex}",
    ], check=True)

    sha = hashlib.sha256()
    with open(enc_path, "rb") as f:
        sha.update(f.read())
    checksum = sha.hexdigest()

    return checksum


def run_backup():
    db_info = parse_db_url(os.getenv("DATABASE_URL", ""))
    backup_dir = Path(os.getenv("BACKUP_DIR", "/data/backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"medical_reports_{timestamp}.sql"
    filepath = backup_dir / filename

    env = os.environ.copy()
    env["PGPASSWORD"] = db_info["password"]

    print(f"[{timestamp}] Starting backup of {db_info['dbname']}...")

    subprocess.run([
        "pg_dump",
        "-h", db_info["host"],
        "-p", db_info["port"],
        "-U", db_info["user"],
        "-d", db_info["dbname"],
        "-F", "p",
        "-f", str(filepath),
        "--no-owner",
        "--no-acl",
    ], env=env, check=True)

    size_mb = filepath.stat().st_size / (1024 * 1024)
    print(f"[{timestamp}] Backup created: {filepath} ({size_mb:.2f} MB)")

    checksum = encrypt_backup(filepath)
    if checksum:
        print(f"[{timestamp}] Encrypted: {filepath}.enc (SHA256: {checksum})")

    # Cleanup old backups (keep last 30 days)
    cutoff = datetime.now(timezone.utc).timestamp() - (30 * 86400)
    for f in backup_dir.glob("medical_reports_*.sql*"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            print(f"[{timestamp}] Cleaned up old backup: {f.name}")

    print(f"[{timestamp}] Backup completed successfully.")


if __name__ == "__main__":
    try:
        run_backup()
    except Exception as e:
        print(f"Backup failed: {e}", file=sys.stderr)
        sys.exit(1)
