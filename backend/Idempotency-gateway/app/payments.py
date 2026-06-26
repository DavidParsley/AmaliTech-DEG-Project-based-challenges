import time
from fastapi import APIRouter, Header, Response, HTTPException
from app.schemas import PaymentRequest, PaymentResponse
from app.store import store

router = APIRouter()


@router.post("/process-payment", response_model=PaymentResponse)
def process_payment(
    payment: PaymentRequest,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    lock = store.get_lock(idempotency_key)

    with lock:
        existing = store.get(idempotency_key)

        if existing is not None:
            if existing["request_body"] != payment.model_dump():
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different request body.",
                )
            response.headers["X-Cache-Hit"] = "true"
            return existing["response_body"]

        time.sleep(2)  
        payment_response = PaymentResponse(
            message=f"Charged {payment.amount:g} {payment.currency}"
        )

        store.save(
            key=idempotency_key,
            request_body=payment.model_dump(),
            response_body=payment_response.model_dump(),
        )

        return payment_response