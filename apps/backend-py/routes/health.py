from fastapi import APIRouter
from config import PROVIDER

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True, "provider": PROVIDER}
