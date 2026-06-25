from fastapi import FastAPI
from app.payments import router as payments_router


app = FastAPI()
app.include_router(payments_router)


@app.get("/")
def health_check():
    return {"status": "alive"}
