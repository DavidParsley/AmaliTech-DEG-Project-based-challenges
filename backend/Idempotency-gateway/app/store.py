class IdempotencyStore:
    def __init__(self):
        self._store: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        return self._store.get(key)

    def save(self, key: str, request_body: dict, response_body: dict) -> None:
        self._store[key] = {
            "request_body": request_body,
            "response_body": response_body,
        }

store = IdempotencyStore()        