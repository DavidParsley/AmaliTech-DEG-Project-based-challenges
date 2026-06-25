import os


IDEMPOTENCY_KEY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_KEY_TTL_SECONDS", "86400"))# I've set the  saved idempotency key to stay  valid for only 24hrs