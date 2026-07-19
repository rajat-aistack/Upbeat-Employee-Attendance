"""
Background sync manager for offline attendance records.
Periodically attempts to sync unsynced records with the API.
"""
import logging
import threading
import time
from typing import Optional

from employee_app.services.offline_store import OfflineStore
from employee_app.services.api_client import APIClient, APIError

logger = logging.getLogger(__name__)


class SyncManager:
    """Manages background synchronization of offline records."""

    def __init__(
        self,
        api_client: APIClient,
        offline_store: OfflineStore,
        interval_seconds: int = 300,
    ):
        self.api_client = api_client
        self.offline_store = offline_store
        self.interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_sync_callback = None

    def set_sync_callback(self, callback):
        """Set a callback to be called after sync attempt (for UI updates)."""
        self._on_sync_callback = callback

    def start(self):
        """Start the background sync thread."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="SyncManager")
        self._thread.start()
        logger.info(f"Sync manager started (interval: {self.interval}s)")

    def stop(self):
        """Stop the background sync thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sync manager stopped")

    def sync_now(self) -> dict:
        """Perform an immediate sync. Returns sync result."""
        return self._do_sync()

    def _run(self):
        """Background thread main loop."""
        while not self._stop_event.is_set():
            # Send keep-alive ping to Render server
            try:
                logger.info("Sending keep-alive ping to API server...")
                self.api_client.check_health()
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}")

            try:
                self._do_sync()
            except Exception as e:
                logger.error(f"Sync error: {e}")

            # Wait for interval or until stopped
            self._stop_event.wait(timeout=self.interval)

    def _do_sync(self) -> dict:
        """Attempt to sync all unsynced records."""
        result = {"synced": 0, "failed": 0, "total": 0}

        unsynced = self.offline_store.get_unsynced_records()
        if not unsynced:
            return result

        result["total"] = len(unsynced)
        logger.info(f"Attempting to sync {len(unsynced)} offline records")

        # Build sync payload
        sync_records = []
        for record in unsynced:
            sync_records.append({
                "action": record["action"],
                "device_fingerprint": record["device_fingerprint"],
                "hostname": record.get("hostname"),
                "system_username": record.get("system_username"),
                "ip_address": record.get("ip_address"),
                "mac_address": record.get("mac_address"),
                "wifi_ssid": record.get("wifi_ssid"),
                "wifi_bssid": record.get("wifi_bssid"),
                "gateway_mac": record.get("gateway_mac"),
                "gateway_ip": record.get("gateway_ip"),
                "timestamp": record["timestamp"],
                "sync_id": record["sync_id"],
            })

        try:
            response = self.api_client.sync_records(sync_records)
            result["synced"] = response.get("synced", 0) + response.get("skipped", 0)
            result["failed"] = len(response.get("errors", []))

            # Mark all as synced (server handles dedup via sync_id)
            for record in unsynced:
                self.offline_store.mark_synced(record["sync_id"])

            logger.info(
                f"Sync complete: {result['synced']} synced, "
                f"{result['failed']} failed"
            )

        except APIError as e:
            logger.error(f"API error during sync: {e}")
            result["failed"] = len(unsynced)
        except Exception as e:
            logger.error(f"Connection error during sync: {e}")
            result["failed"] = len(unsynced)

        # Notify UI
        if self._on_sync_callback:
            try:
                self._on_sync_callback(result)
            except Exception:
                pass

        return result
