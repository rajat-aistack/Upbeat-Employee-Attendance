"""
Local SQLite storage for offline attendance records.
Stores punches when the API server is unreachable, for later sync.
"""
import sqlite3
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from employee_app.config import LOCAL_DB_PATH

logger = logging.getLogger(__name__)


class OfflineStore:
    """Manages local SQLite database for offline attendance records."""

    def __init__(self, db_path: Path = None):
        self.db_path = str(db_path or LOCAL_DB_PATH)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create the offline records table if it doesn't exist."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_id TEXT UNIQUE NOT NULL,
                    action TEXT NOT NULL,
                    device_fingerprint TEXT NOT NULL,
                    hostname TEXT,
                    system_username TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    wifi_ssid TEXT,
                    wifi_bssid TEXT,
                    gateway_mac TEXT,
                    gateway_ip TEXT,
                    timestamp TEXT NOT NULL,
                    synced INTEGER DEFAULT 0,
                    synced_at TEXT,
                    created_at TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            conn.commit()
            logger.info("Offline store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize offline store: {e}")
        finally:
            conn.close()

    def store_record(
        self,
        action: str,
        device_fingerprint: str,
        hostname: Optional[str] = None,
        system_username: Optional[str] = None,
        ip_address: Optional[str] = None,
        mac_address: Optional[str] = None,
        wifi_ssid: Optional[str] = None,
        wifi_bssid: Optional[str] = None,
        gateway_mac: Optional[str] = None,
        gateway_ip: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Store an offline attendance record. Returns the sync_id."""
        sync_id = str(uuid.uuid4())
        now = timestamp or datetime.utcnow()

        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO offline_records 
                (sync_id, action, device_fingerprint, hostname, system_username,
                 ip_address, mac_address, wifi_ssid, wifi_bssid, 
                 gateway_mac, gateway_ip, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sync_id, action, device_fingerprint, hostname, system_username,
                ip_address, mac_address, wifi_ssid, wifi_bssid,
                gateway_mac, gateway_ip,
                now.isoformat(), datetime.utcnow().isoformat(),
            ))
            conn.commit()
            logger.info(f"Stored offline {action} record: {sync_id}")
            return sync_id
        except Exception as e:
            logger.error(f"Failed to store offline record: {e}")
            raise
        finally:
            conn.close()

    def get_unsynced_records(self) -> List[Dict[str, Any]]:
        """Get all records that haven't been synced yet."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM offline_records WHERE synced = 0 ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def mark_synced(self, sync_id: str):
        """Mark a record as successfully synced."""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE offline_records SET synced = 1, synced_at = ? WHERE sync_id = ?",
                (datetime.utcnow().isoformat(), sync_id),
            )
            conn.commit()
            logger.info(f"Marked record {sync_id} as synced")
        finally:
            conn.close()

    def mark_error(self, sync_id: str, error: str):
        """Mark a record with a sync error."""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE offline_records SET error_message = ? WHERE sync_id = ?",
                (error, sync_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_unsynced_count(self) -> int:
        """Get count of unsynced records."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM offline_records WHERE synced = 0"
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def cleanup_old_synced(self, days: int = 30):
        """Remove synced records older than specified days."""
        conn = self._get_conn()
        try:
            conn.execute(
                "DELETE FROM offline_records WHERE synced = 1 AND synced_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            conn.commit()
        finally:
            conn.close()
