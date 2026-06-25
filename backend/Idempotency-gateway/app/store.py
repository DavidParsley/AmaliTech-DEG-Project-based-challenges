import threading

class IdempotencyStore:
    def __init__(self):
        self._store: dict[str, dict] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        return self._store.get(key)

    def save(self, key: str, request_body: dict, response_body: dict) -> None:
        self._store[key] = {
            "request_body": request_body,
            "response_body": response_body,
        }

    def get_lock(self, key: str) -> threading.Lock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]


store = IdempotencyStore()