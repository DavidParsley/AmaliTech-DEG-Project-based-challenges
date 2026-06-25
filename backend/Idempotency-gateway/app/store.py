import threading
import time

from app.config import IDEMPOTENCY_KEY_TTL_SECONDS


class IdempotencyStore:
    def __init__(self):
        self._store: dict[str, dict] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        if time.time() - entry["created_at"] > IDEMPOTENCY_KEY_TTL_SECONDS:
            # if its expired forget it (current set upis 24hrs). Next request with this key is treated as brand new not as a conflict and not as a cache.
            del self._store[key]
            return None

        return entry

    def save(self, key: str, request_body: dict, response_body: dict) -> None:
        self._store[key] = {
            "request_body": request_body,
            "response_body": response_body,
            "created_at": time.time(),
        }

    def get_lock(self, key: str) -> threading.Lock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]


store = IdempotencyStore()