from fastapi import APIRouter

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/x")
def webhook_placeholder() -> dict[str, str]:
    return {"status": "not_implemented"}
