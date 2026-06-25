from fastapi import APIRouter, Header
from app.schemas import PaymentRequest, PaymentResponse
from app.store import store
from app.store import IdempotencyStore


router = APIRouter()


@router.post("/process-payment", response_model=PaymentResponse)
def process_payment(
    payment: PaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    response = PaymentResponse(
        message=f"Charged {payment.amount} {payment.currency}"
    )

    store.save(
        key=idempotency_key,
        request_body=payment.model_dump(),
        response_body=response.model_dump(),
    )

    return response