import threading
import time

from fastapi.testclient import TestClient

from app import store as store_module
from app.main import app

client = TestClient(app)


def test_story1_happy_path_new_key_returns_200():
    response = client.post(
        "/process-payment",
        headers={"Idempotency-Key": "test-key-story1"},
        json={"amount": 50, "currency": "GHS"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Charged 50.0 GHS"}
    assert "x-cache-hit" not in response.headers


def test_story2_duplicate_same_key_same_body_returns_cached():
    headers = {"Idempotency-Key": "test-key-story2"}
    body = {"amount": 75, "currency": "USD"}

    first = client.post("/process-payment", headers=headers, json=body)
    assert first.status_code == 200
    assert "x-cache-hit" not in first.headers

    second = client.post("/process-payment", headers=headers, json=body)
    assert second.status_code == 200
    assert second.headers["x-cache-hit"] == "true"
    assert second.json() == first.json()


def test_story3_same_key_different_body_returns_409():
    headers = {"Idempotency-Key": "test-key-story3"}

    first = client.post(
        "/process-payment", headers=headers, json={"amount": 10, "currency": "GHS"}
    )
    assert first.status_code == 200

    second = client.post(
        "/process-payment", headers=headers, json={"amount": 20, "currency": "GHS"}
    )
    assert second.status_code == 409
    assert "detail" in second.json()


def test_bonus_concurrent_identical_requests_do_not_double_process():
    headers = {"Idempotency-Key": "test-key-bonus-race"}
    body = {"amount": 15, "currency": "GHS"}

    results = {}

    def make_request(label):
        start = time.monotonic()
        resp = client.post("/process-payment", headers=headers, json=body)
        elapsed = time.monotonic() - start
        results[label] = (resp, elapsed)

    t1 = threading.Thread(target=make_request, args=("a",))
    t2 = threading.Thread(target=make_request, args=("b",))

    t1.start()
    time.sleep(0.2)
    t2.start()

    t1.join()
    t2.join()

    resp_a, elapsed_a = results["a"]
    resp_b, elapsed_b = results["b"]

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    # Only one request should carry the cache-hit header.
    cache_hits = [r.headers.get("x-cache-hit") == "true" for r in (resp_a, resp_b)]
    assert cache_hits.count(True) == 1

    # Cache hit should resolve well under a full 2s processing run.
    elapsed_of_cache_hit = elapsed_a if cache_hits[0] else elapsed_b
    assert elapsed_of_cache_hit < 1.9


def test_developers_choice_ttl_expiry_resets_key(monkeypatch):
    # Override TTL for this test only; restored automatically after.
    monkeypatch.setattr(store_module, "IDEMPOTENCY_KEY_TTL_SECONDS", 1)

    headers = {"Idempotency-Key": "test-key-ttl"}

    first = client.post(
        "/process-payment", headers=headers, json={"amount": 1, "currency": "GHS"}
    )
    assert first.status_code == 200

    time.sleep(1.5)

    # Same key, different body, but expired  should reprocess, not 409.
    second = client.post(
        "/process-payment", headers=headers, json={"amount": 2, "currency": "USD"}
    )
    assert second.status_code == 200
    assert second.json() == {"message": "Charged 2.0 USD"}